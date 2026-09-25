from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from tqdm.auto import tqdm

def normalize_sinogram(sino: torch.Tensor) -> tuple[torch.Tensor, float, float]:
    """Min-max normalize to [0, 1]. Returns (normalized, shift, scale): sino = norm * scale + shift."""
    shift = sino.min().item()
    scale = max(sino.max().item() - shift, 1e-12)
    return (sino - shift) / scale, shift, scale


def generate_coordinate_grid(height: int, width: int, device: torch.device | str = "cpu") -> torch.Tensor:
    """(1, H, W, 2) grid in [-1, 1]; last dim is (x=detector, y=angle) as grid_sample expects."""
    ys = torch.linspace(-1.0, 1.0, height, device=device)
    xs = torch.linspace(-1.0, 1.0, width, device=device)
    gy, gx = torch.meshgrid(ys, xs, indexing="ij")
    return torch.stack([gx, gy], dim=-1).unsqueeze(0)


@torch.no_grad()
def detect_defective_columns(sinogram: torch.Tensor, threshold: float = 1e-6) -> torch.Tensor:
    """Eq. (3). Returns (M, N) float mask: 1 = non-defective, 0 = defective (whole detector column)."""
    mean_angular_grad = (sinogram[1:] - sinogram[:-1]).abs().mean(dim=0)  # (N,)
    valid = (mean_angular_grad > threshold).to(sinogram.dtype)
    return valid.unsqueeze(0).expand_as(sinogram)


def angular_sort_indices(reference: torch.Tensor) -> torch.Tensor:
    """Per-detector-column ascending sort indices along the angular axis (dim 0). Non-differentiable."""
    return torch.sort(reference.detach(), dim=0, stable=True).indices

class MultiResolutionGrid(nn.Module):
    """Learnable feature grids at 1/4, 1/3, 1/2 of the sinogram size, sampled bilinearly."""

    def __init__(self, base_shape, divisors=(4, 3, 2), features_per_level=2, init_range=1e-4):
        super().__init__()
        H, W = base_shape
        self.grids = nn.ParameterList()
        for d in divisors:
            g = torch.empty(1, features_per_level, max(H // d, 2), max(W // d, 2))
            self.grids.append(nn.Parameter(g.uniform_(-init_range, init_range)))
        self.out_features = features_per_level * len(divisors)

    def forward(self, coords: torch.Tensor) -> torch.Tensor:
        """coords (1, H, W, 2) -> features (1, H, W, C)."""
        feats = [
            F.grid_sample(g, coords, mode="bilinear", padding_mode="border", align_corners=True)
            for g in self.grids
        ]
        return torch.cat(feats, dim=1).permute(0, 2, 3, 1)


class IdealSinogramNet(nn.Module):
    """F_Theta: multi-resolution grid + ReLU MLP -> ideal sinogram value per coordinate."""

    def __init__(self, sino_shape, hidden_dim=64, num_hidden_layers=3,
                 features_per_level=2, divisors=(4, 3, 2)):
        super().__init__()
        self.grid = MultiResolutionGrid(sino_shape, divisors, features_per_level)
        layers, in_dim = [], self.grid.out_features
        for _ in range(num_hidden_layers):
            layers += [nn.Linear(in_dim, hidden_dim), nn.ReLU(inplace=True)]
            in_dim = hidden_dim
        layers.append(nn.Linear(in_dim, 1))
        self.mlp = nn.Sequential(*layers)

    def forward(self, coords: torch.Tensor) -> torch.Tensor:
        """coords (1, M, N, 2) -> (M, N)."""
        return self.mlp(self.grid(coords))[0, ..., 0]


class StripeArtifactNet(nn.Module):
    """F_Phi. mode="column": one additive offset per detector column (log(1/C_m), Eq. 2),
    high-passed so it can only hold stripes narrower than ~`highpass` px.
    mode="matrix": the paper's free (M, N) matrix; relies on the sparsity loss to stay column-like."""

    def __init__(self, shape, mode="column", highpass=41, init_range=1e-4):
        super().__init__()
        M, N = shape
        self.param = nn.Parameter(
            torch.empty(1 if mode == "column" else M, N).uniform_(-init_range, init_range)
        )
        k = highpass if (mode == "column" and highpass) else None
        if k is not None:
            k = k + 1 if k % 2 == 0 else k
            k = k if k < N else None
        self.k = k

    def forward(self) -> torch.Tensor:
        """(1, N) in column mode, (M, N) in matrix mode."""
        if self.k is None:
            return self.param
        smooth = F.avg_pool1d(self.param.unsqueeze(0), self.k, stride=1,
                              padding=self.k // 2, count_include_pad=False)
        return self.param - smooth.squeeze(0)
    
def ideal_smoothness_loss(p_is_sorted, n_ref, circular=True, detach_weights=True):
    """Psi_IS (Eq. 7) = ||W * grad_det(P_IS_sorted)||_2, W = P_IS_sorted / max|P_IS_sorted|.
    detach_weights=True treats W as fixed coefficients. With gradients through W and its max,
    the loss can be reduced by inflating a few pixels instead of smoothing.
    n_ref = M*N of the full sinogram, so the value is the literal norm even in column-batch mode."""
    ref = p_is_sorted.detach() if detach_weights else p_is_sorted
    w = ref / ref.abs().max().clamp_min(1e-8)
    if circular:
        grad = p_is_sorted - torch.roll(p_is_sorted, shifts=-1, dims=1)
    else:
        grad, w = p_is_sorted[:, :-1] - p_is_sorted[:, 1:], w[:, :-1]
    return torch.sqrt(((w * grad) ** 2).mean() * n_ref + 1e-12)


def stripe_sparsity_loss(p_sa_sorted, n_ref, circular=True):
    """Psi_SA (Eq. 8) = ||grad_ang(P_SA_sorted)||_1 (literal sum via n_ref)."""
    if circular:
        grad = p_sa_sorted - torch.roll(p_sa_sorted, shifts=-1, dims=0)
    else:
        grad = p_sa_sorted[:-1] - p_sa_sorted[1:]
    return grad.abs().mean() * n_ref

@dataclass
class INRDestripeConfig:
    iterations: int = 5000
    lr: float = 1e-4
    kappa: float = 1.0
    defect_threshold: float = 1e-6
    lam_is: tuple[float, float] = (1e-4, 5e-3)   # (start, end), linear ramp
    lam_sa: tuple[float, float] = (1e-4, 1e-3)   # matrix mode only
    stripe_mode: str = "matrix"                  # "column" or "matrix"
    stripe_highpass: int | None = 41             # column mode: max stripe width in px (None = off)
    center_stripes: bool = False                 # zero-mean P_SA over valid detector columns
    nonneg_weight: float = 0.0                   # soft ReLU penalty on negative P_IS values
    features_per_level: int = 2
    hidden_dim: int = 64
    num_hidden_layers: int = 3
    batch_cols: int | None = None
    seed: int | None = 0
    device: str | None = None
    circular_gradients: bool = True      # wrap-around differences from Eq. 7 and 8
    detach_weights: bool = True         # paper does not stop gradients through W_IS


class DestripeResult(NamedTuple):
    corrected: np.ndarray           # P_IS^out in original units, (M, N)
    ideal: np.ndarray               # P_IS before residual compensation
    stripes: np.ndarray             # P_SA expanded to (M, N)
    defective_columns: np.ndarray   # (N,) bool


@torch.no_grad()
def predict_ideal(net, coords, chunk=512):
    return torch.cat(
        [net(coords[:, :, j:j + chunk]) for j in range(0, coords.shape[2], chunk)], dim=1
    )


def residual_compensation(p_raw, p_is, p_sa, valid_mask, kappa=1.0):
    """Eq. (10), non-defective pixels only."""
    E = p_raw - (p_is + p_sa)
    E_tilde = E - E.mean(dim=0, keepdim=True)
    return p_is + kappa * p_is * E_tilde * valid_mask


def train_inr_destriping(sinogram, cfg: INRDestripeConfig | None = None) -> DestripeResult:
    cfg = cfg or INRDestripeConfig()
    if cfg.stripe_mode not in ("column", "matrix"):
        raise ValueError("stripe_mode must be 'column' or 'matrix'")
    device = cfg.device or ("cuda" if torch.cuda.is_available() else "cpu")
    if cfg.seed is not None:
        torch.manual_seed(cfg.seed)

    sino = torch.as_tensor(sinogram, dtype=torch.float32, device=device)
    if sino.ndim != 2:
        raise ValueError(f"Expected a 2D (angles, detectors) sinogram, got {tuple(sino.shape)}")
    if not torch.isfinite(sino).all():
        raise ValueError("Sinogram contains NaN/Inf; replace them (e.g. with 0) first.")

    p_raw, shift, scale = normalize_sinogram(sino)
    M, N = p_raw.shape
    n_ref = float(M * N)
    coords = generate_coordinate_grid(M, N, device)
    valid = detect_defective_columns(p_raw, cfg.defect_threshold)

    net_is = IdealSinogramNet(
        (M, N), hidden_dim=cfg.hidden_dim, num_hidden_layers=cfg.num_hidden_layers,
        features_per_level=cfg.features_per_level,
    ).to(device)
    net_sa = StripeArtifactNet((M, N), mode=cfg.stripe_mode, highpass=cfg.stripe_highpass).to(device)
    optimizer = torch.optim.Adam([*net_is.parameters(), *net_sa.parameters()], lr=cfg.lr)

    def stripe_field():
        sa = net_sa()
        if cfg.center_stripes:
            sa = sa - (sa * valid).sum() / valid.sum().clamp_min(1.0)
        return sa

    batch = cfg.batch_cols if (cfg.batch_cols and cfg.batch_cols < N) else None
    if batch is not None and batch < 2:
        raise ValueError("batch_cols must be >= 2")

    pbar = tqdm(range(cfg.iterations), desc="Optimizing INR")
    for step in pbar:
        if batch:
            j0 = torch.randint(0, N - batch + 1, (1,)).item()
            cols = slice(j0, j0 + batch)
        else:
            cols = slice(None)

        p_is = net_is(coords[:, :, cols])
        p_sa = stripe_field()[:, cols].expand(M, -1)
        target, mask = p_raw[:, cols], valid[:, cols]

        fidelity = ((p_is + p_sa - target).abs() * mask).sum() / mask.sum().clamp_min(1.0)

        idx = angular_sort_indices(p_is)                  # sort by predicted IS (Algorithm 1)
        p_is_sorted = torch.gather(p_is, 0, idx)

        t = step / max(cfg.iterations - 1, 1)
        lam_is = cfg.lam_is[0] + (cfg.lam_is[1] - cfg.lam_is[0]) * t
        loss = fidelity + lam_is * ideal_smoothness_loss(
            p_is_sorted, n_ref, cfg.circular_gradients, cfg.detach_weights)

        if cfg.stripe_mode == "matrix":
            lam_sa = cfg.lam_sa[0] + (cfg.lam_sa[1] - cfg.lam_sa[0]) * t
            loss = loss + lam_sa * stripe_sparsity_loss(
                torch.gather(p_sa, 0, idx), n_ref, cfg.circular_gradients)

        if cfg.nonneg_weight > 0:
            loss = loss + cfg.nonneg_weight * F.relu(-p_is).mean()

        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()

        if step % 500 == 0:
            pbar.set_postfix(loss=f"{loss.item():.4f}", l1=f"{fidelity.item():.4f}")

    with torch.no_grad():
        p_is = predict_ideal(net_is, coords)
        p_sa = stripe_field().expand(M, -1)
        p_out = residual_compensation(p_raw, p_is, p_sa, valid, cfg.kappa)

        to_np = lambda x: x.detach().contiguous().cpu().numpy()
        return DestripeResult(
            corrected=to_np(p_out * scale + shift),
            ideal=to_np(p_is * scale + shift),
            stripes=to_np(p_sa * scale),
            defective_columns=to_np(valid[0] == 0),
        )