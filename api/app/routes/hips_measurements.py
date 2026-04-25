from app.models.body_metric import HipsMeasurement
from app.routes._body_metric_crud import make_body_metric_blueprint
from app.services.body_metrics import HIPS

bp = make_body_metric_blueprint("hips_measurements", HipsMeasurement, HIPS)
