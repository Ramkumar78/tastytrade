import os
import logging
from flask import Flask, jsonify, request, send_from_directory
from tastytrade import Session, Account
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Set static folder to where Dockerfile puts the build
app = Flask(__name__, static_folder='static/dist')

def get_session():
    provider_secret = os.getenv('TT_SECRET')
    refresh_token = os.getenv('TT_REFRESH_TOKEN') or os.getenv('TT_CLIENT_ID')
    is_test = os.getenv('TT_IS_TEST', 'False').lower() == 'true'

    if not refresh_token:
        raise ValueError("Missing TT_REFRESH_TOKEN (or TT_CLIENT_ID)")

    if "." not in refresh_token:
        logger.warning("Provided token does not look like a JWT (no dots found). Ensure you are using a valid Refresh Token, not just a Client ID.")

    return Session(
        provider_secret=provider_secret,
        refresh_token=refresh_token,
        is_test=is_test
    )

@app.route('/api/auth/status')
def get_status():
    logger.info("Checking auth status...")
    try:
        session = get_session()
        logger.info("Session initialized for auth check.")
        if session.validate():
            logger.info("Session validated successfully.")
            return jsonify({"status": "connected", "message": "🟢 CASINO BRIDGE ACTIVE"})

        logger.warning("Session validation failed.")
        return jsonify({"status": "error", "message": "🛑 AUTH FAILED"})
    except Exception as e:
        logger.error(f"Auth status error: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/account/metrics')
def get_metrics():
    # Thalaiva Logic: Defend the $10,000 line
    logger.info("Fetching account metrics...")
    try:
        session = get_session()
        logger.info("Session initialized for metrics.")

        accounts = Account.get_accounts(session)
        logger.info(f"Accounts fetched. Count: {len(accounts)}")

        if not accounts:
             logger.warning("No accounts found.")
             return jsonify({"error": "No accounts found"}), 404

        # We target your main margin account
        acc = accounts[0]
        logger.info(f"Using account: {acc.account_number}")

        balances = acc.get_balances(session)
        positions = acc.get_positions(session)

        net_liq = float(balances.net_liquidating_value)
        used_bp = float(balances.used_derivative_buying_power)
        logger.info(f"Balances: Net Liq={net_liq}, Used BP={used_bp}")

        # Calculation for Thalaiva's 30% BP Rule
        bp_usage = (used_bp / net_liq) * 100 if net_liq > 0 else 0
        logger.info(f"Calculated BP Usage: {bp_usage}%")

        return jsonify({
            "net_liq": round(net_liq, 2),
            "bp_usage": round(bp_usage, 2),
            "available_bp": round(float(balances.derivative_buying_power), 2),
            "verdict": "🟢 CLEAR" if bp_usage < 30 else "🛑 CEASE TRADING",
            "positions_count": len(positions)
        })
    except Exception as e:
        logger.error(f"Error fetching metrics: {e}", exc_info=True)
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
    logger.info("Starting Thalaiva Command Server...")
    app.run(host='0.0.0.0', port=5000)
