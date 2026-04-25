from app.models.body_metric import MuscleMassLog
from app.routes._body_metric_crud import make_body_metric_blueprint
from app.services.body_metrics import MUSCLE_MASS

bp = make_body_metric_blueprint("muscle_mass_logs", MuscleMassLog, MUSCLE_MASS)
