from app.models.body_metric import BodyFatLog
from app.routes._body_metric_crud import make_body_metric_blueprint
from app.services.body_metrics import BODY_FAT

bp = make_body_metric_blueprint("body_fat_logs", BodyFatLog, BODY_FAT)
