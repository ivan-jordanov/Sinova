"""Quick integration test for Phase 1."""
import numpy as np
from app.services.business.job_manager import get_job_manager
from app.services.business.operation_executor import (
    apply_single_operation,
    apply_operations_to_data,
)
from app.schemas.preprocessing import Operation, PreprocessingConfiguration

def test_normalization():
    """Test normalize operation."""
    data = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)
    op = Operation(
        id="1", name="Normalize", short_name="normalize",
        category="intensity", enabled=True, scope="slice"
    )
    result = apply_single_operation(data, op)
    assert result.min() >= 0.0 and result.max() <= 1.0
    print("✓ Normalization works")

def test_job_manager():
    """Test job creation and status tracking."""
    jm = get_job_manager()
    
    # Create a job
    config = PreprocessingConfiguration(operations=[])
    job_id = jm.create_job(config)
    assert job_id is not None
    print(f"✓ Created job: {job_id}")
    
    # Check status
    job = jm.get_job(job_id)
    assert job is not None
    assert job.status == "queued"
    print(f"✓ Job status: {job.status}")
    
    # Start job
    jm.start_job(job_id)
    job = jm.get_job(job_id)
    assert job.status == "running"
    print(f"✓ Job started")
    
    # Update progress
    jm.update_progress(job_id, 50, "Half done")
    job = jm.get_job(job_id)
    assert job.progress == 50
    print(f"✓ Progress updated: {job.progress}%")
    
    # Complete job
    jm.complete_job(job_id)
    job = jm.get_job(job_id)
    assert job.status == "completed"
    assert job.progress == 100
    print(f"✓ Job completed")

def test_operation_chain():
    """Test applying multiple operations."""
    data = np.random.rand(4, 4).astype(np.float32)
    
    ops = [
        Operation(
            id="1", name="Normalize", short_name="normalize",
            category="intensity", enabled=True, scope="slice"
        ),
        Operation(
            id="2", name="Denoise", short_name="denoise",
            category="spatial", enabled=True, scope="slice",
            parameters={"method": "gaussian", "sigma": 0.5}
        ),
    ]
    
    config = PreprocessingConfiguration(operations=ops)
    result = apply_operations_to_data(data, config)
    
    assert result.shape == data.shape
    assert result.dtype == np.float32
    print("✓ Operation chain works")

if __name__ == "__main__":
    print("Testing Phase 1 components...\n")
    test_normalization()
    test_job_manager()
    test_operation_chain()
    print("\n✓ All Phase 1 tests passed!")
