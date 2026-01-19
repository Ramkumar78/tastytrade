import os
from flask import Flask, jsonify, request, send_from_directory
from tastytrade import Session, Account
from dotenv import load_dotenv

load_dotenv()

# Set static folder to where Dockerfile puts the build
app = Flask(__name__, static_folder='static/dist')

@app.route('/api/auth/status')
def get_status():
    try:
        # Initializing session with your credentials
        session = Session(
            provider_secret=os.getenv('TT_SECRET'),
            refresh_token=os.getenv('TT_CLIENT_ID')
        )
        if session.validate():
            return jsonify({"status": "connected", "message": "🟢 CASINO BRIDGE ACTIVE"})
        return jsonify({"status": "error", "message": "🛑 AUTH FAILED"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/account/metrics')
def get_metrics():
    # Thalaiva Logic: Defend the $10,000 line
    try:
        session = Session(provider_secret=os.getenv('TT_SECRET'), refresh_token=os.getenv('TT_CLIENT_ID'))
        accounts = Account.get_accounts(session)
        if not accounts:
             return jsonify({"error": "No accounts found"}), 404

        # We target your main margin account
        acc = accounts[0]

        balances = acc.get_balances(session)
        positions = acc.get_positions(session)

        net_liq = float(balances.net_liquidating_value)
        # Calculation for Thalaiva's 30% BP Rule
        used_bp = float(balances.used_derivative_buying_power)
        bp_usage = (used_bp / net_liq) * 100 if net_liq > 0 else 0

        return jsonify({
            "net_liq": round(net_liq, 2),
            "bp_usage": round(bp_usage, 2),
            "available_bp": round(float(balances.derivative_buying_power), 2),
            "verdict": "🟢 CLEAR" if bp_usage < 30 else "🛑 CEASE TRADING",
            "positions_count": len(positions)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve React App
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path.startswith('api/'):
        return jsonify({"error": "Not Found"}), 404

    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
