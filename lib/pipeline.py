from model import analyze
from db import save_analysis, save_predictions

def run_analysis(headlines):
    text, preds = analyze(headlines)
    analysis_id = save_analysis(headlines, text)
    save_predictions(analysis_id, preds)
    return analysis_id, text
