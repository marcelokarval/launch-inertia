# Shared core components
#
# IMPORTANT: Do not import models at module level to avoid AppRegistryNotReady errors.
# Import directly from submodules where needed:
#
#   from core.shared.models.base import BaseModel
#   from core.shared.models.mixins import TimestampMixin, SoftDeleteMixin, ...
#   from core.shared.managers.base import BaseManager, BaseQuerySet
#
default_app_config = "core.shared.apps.SharedConfig"
