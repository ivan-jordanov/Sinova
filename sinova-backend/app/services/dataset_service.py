from app.schemas.dataset import DatasetMetadata


MOCK_METADATA = DatasetMetadata(
    name="spider.mraw",
    detector_width=2048,
    detector_height=2048,
    projections=1800,
    slices=2048,
    format="MRAW",
)


def get_metadata() -> DatasetMetadata:
    return MOCK_METADATA


def load_dataset(path: str) -> DatasetMetadata:
    """Return placeholder metadata until real file inspection is implemented."""
    return MOCK_METADATA.model_copy(update={"name": path.rsplit("/", 1)[-1]})