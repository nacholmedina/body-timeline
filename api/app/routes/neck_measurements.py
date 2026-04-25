from app.models.body_metric import NeckMeasurement
from app.routes._body_metric_crud import make_body_metric_blueprint
from app.services.body_metrics import NECK

bp = make_body_metric_blueprint("neck_measurements", NeckMeasurement, NECK)
