"""
Flask Web Application for LightGBM Trading Tool
No-code interface for extracting trading signals from Excel files
"""

from flask import Flask, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime
import json

from excel_analyzer import ExcelAnalyzer
from model_trainer import ModelTrainer
from rule_extractor import RuleExtractor
from rule_simplifier import create_trader_friendly_rules, export_trader_rules_to_excel

app = Flask(__name__)
app.secret_key = 'lightgbm_trading_tool_secret_key_2025'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Auto-reload templates (no caching)

# Create necessary directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Home page - file upload"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload Excel (.xlsx, .xls) or CSV file'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        file.save(filepath)
        
        # Analyze file
        analyzer = ExcelAnalyzer(filepath)
        analyzer.load_file()
        analysis = analyzer.analyze_structure()
        recommendations = analyzer.get_feature_target_recommendation()
        
        # Store in session
        session['filepath'] = filepath
        session['filename'] = filename
        
        # Return analysis results
        return jsonify({
            'success': True,
            'filename': filename,
            'rows': analysis['basic_info']['rows'],
            'columns': analysis['basic_info']['columns'],
            'column_names': analysis['basic_info']['column_names'],
            'datetime_columns': analysis['datetime_columns'],
            'numeric_columns': analysis['numeric_columns']['all_numeric'],
            'recommended_features': recommendations['recommended_features'],
            'recommended_targets': recommendations['recommended_targets'],
            'missing_data': analysis['missing_data']
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/train', methods=['POST'])
def train_model():
    """Train LightGBM model with selected parameters"""
    try:
        # Get parameters from request
        data = request.json
        feature_columns = data.get('features', [])
        target_column = data.get('target')
        task_type = data.get('task_type', 'regression')
        
        # Hyperparameters
        n_estimators = int(data.get('n_estimators', 100))
        learning_rate = float(data.get('learning_rate', 0.05))
        max_depth = int(data.get('max_depth', 5))
        
        if not feature_columns or not target_column:
            return jsonify({'error': 'Please select features and target'}), 400
        
        # Load file from session
        filepath = session.get('filepath')
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found. Please upload again.'}), 400
        
        # Load data
        analyzer = ExcelAnalyzer(filepath)
        analyzer.load_file()
        recommendations = analyzer.get_feature_target_recommendation()
        
        # Train model
        trainer = ModelTrainer(
            df=analyzer.df,
            feature_columns=feature_columns,
            target_column=target_column,
            datetime_column=recommendations['datetime_column'],
            task_type=task_type
        )
        
        # Update hyperparameters
        trainer.update_hyperparameters({
            'n_estimators': n_estimators,
            'learning_rate': learning_rate,
            'max_depth': max_depth
        })
        
        # Prepare and train
        prep_stats = trainer.prepare_data(test_size=0.2, use_time_series_split=True)
        train_results = trainer.train(verbose=False)
        
        # Get feature importance
        importance_df = trainer.get_feature_importance()
        feature_importance = importance_df.to_dict('records')
        
        # Extract rules
        extractor = RuleExtractor(
            model=trainer.model,
            feature_names=feature_columns,
            X_train=trainer.X_train,
            task_type=task_type
        )
        
        rules = extractor.extract_rules(max_rules=20, min_samples=5)
        
        # Simplify rules for traders
        simplified_rules = create_trader_friendly_rules(rules, top_n=6, min_coverage=0.15)
        
        # Convert to dict for JSON
        trading_signals = []
        for idx, rule in enumerate(simplified_rules, 1):
            signal_dict = rule.to_dict(asset="SPY")
            signal_dict['rule_number'] = idx
            signal_dict['readable_text'] = rule.to_readable_text("SPY")
            trading_signals.append(signal_dict)
        
        # Generate output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Feature importance file
        importance_file = os.path.join(app.config['OUTPUT_FOLDER'], f'feature_importance_{timestamp}.xlsx')
        with pd.ExcelWriter(importance_file, engine='openpyxl') as writer:
            importance_df.to_excel(writer, sheet_name='Feature Importance', index=False)
            worksheet = writer.sheets['Feature Importance']
            for idx, col in enumerate(importance_df.columns):
                max_length = max(importance_df[col].astype(str).map(len).max(), len(str(col))) + 2
                column_width = min(max(max_length, 15), 50)
                worksheet.column_dimensions[chr(65 + idx)].width = column_width
        
        # Trading signals file
        signals_file = os.path.join(app.config['OUTPUT_FOLDER'], f'trading_signals_{timestamp}.xlsx')
        export_trader_rules_to_excel(simplified_rules, signals_file, asset="SPY")
        
        # Store file paths in session
        session['importance_file'] = importance_file
        session['signals_file'] = signals_file
        
        # Return results
        return jsonify({
            'success': True,
            'feature_importance': feature_importance,
            'trading_signals': trading_signals,
            'model_performance': {
                'task_type': train_results['task_type'],
                'train_metrics': train_results['train_metrics'],
                'test_metrics': train_results['test_metrics']
            },
            'data_stats': prep_stats,
            'importance_file': os.path.basename(importance_file),
            'signals_file': os.path.basename(signals_file)
        })
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("="*80)
        print("ERROR IN /train ENDPOINT:")
        print("="*80)
        print(error_trace)
        print("="*80)
        return jsonify({
            'error': str(e),
            'details': error_trace.split('\n')[-3:-1]  # Last 2 lines of error
        }), 500


@app.route('/download/<file_type>')
def download_file(file_type):
    """Download generated files"""
    try:
        if file_type == 'importance':
            filepath = session.get('importance_file')
        elif file_type == 'signals':
            filepath = session.get('signals_file')
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(filepath, as_attachment=True)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'LightGBM Trading Tool API is running'})


@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    return send_file('templates/favicon.svg', mimetype='image/svg+xml')


@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler to ensure JSON responses"""
    import traceback
    error_trace = traceback.format_exc()
    print("="*80)
    print("UNHANDLED ERROR:")
    print("="*80)
    print(error_trace)
    print("="*80)
    
    # Return JSON error instead of HTML
    return jsonify({
        'error': str(error),
        'type': error.__class__.__name__
    }), 500


if __name__ == '__main__':
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    print("\n" + "="*80)
    print("  LightGBM Trading Tool - Web Interface")
    print("="*80)
    print("\n  Starting server...")
    print(f"\n  Access the web interface at:")
    print(f"    Local:    http://localhost:5000")
    print(f"    Network:  http://{local_ip}:5000")
    print(f"    External: http://95.217.98.112:5000")
    print("\n  Press CTRL+C to stop the server")
    print("="*80 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

