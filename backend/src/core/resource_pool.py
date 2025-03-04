from typing import Generic, TypeVar, Callable, List
from contextlib import contextmanager

T = TypeVar('T')

class ResourcePool(Generic[T]):
    def __init__(
        self, 
        create_resource: Callable[[], T],
        cleanup_resource: Callable[[T], None],
        pool_size: int = 5
    ):
        self.create = create_resource
        self.cleanup = cleanup_resource
        self.pool: List[T] = []
        self.pool_size = pool_size

    @contextmanager
    def acquire(self):
        resource = self._get_resource()
        try:
            yield resource
        finally:
            self._return_resource(resource)

    def _get_resource(self) -> T:
        if not self.pool:
            return self.create()
        return self.pool.pop()

    def _return_resource(self, resource: T):
        if len(self.pool) < self.pool_size:
            self.pool.append(resource)
        else:
            self.cleanup(resource)

# Usage example:
import cv2

camera_pool = ResourcePool(
    create_resource=lambda: cv2.VideoCapture(0),
    cleanup_resource=lambda cam: cam.release(),
    pool_size=3
)

with camera_pool.acquire() as camera:
    ret, frame = camera.read()
    # Process frame 