import os
import logging
from flask import Flask, jsonify, request, send_from_directory
from tastytrade import Session, Account
from tastytrade.utils import TastytradeError
from dotenv import load_dotenv
from legacy_session import LegacySession

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__, static_folder='static/dist')

# Global session for interactive login
current_session = None

def get_session():
    global current_session

    # 1. Use existing interactive session if valid
    if current_session:
        return current_session

    # 2. Try .env credentials
    provider_secret = os.getenv('TT_SECRET')
    refresh_token = os.getenv('TT_REFRESH_TOKEN') or os.getenv('TT_CLIENT_ID')
    is_test = os.getenv('TT_IS_TEST', 'False').lower() == 'true'

    if refresh_token and "." in refresh_token and provider_secret:
        try:
            # We cache it only if successfully created
            if not current_session:
                logger.info("Initializing session from .env credentials...")
                session = Session(
                    provider_secret=provider_secret,
                    refresh_token=refresh_token,
                    is_test=is_test
                )
                current_session = session
                return session
        except Exception as e:
            logger.error(f"Failed to initialize session from .env: {e}")

    return None

@app.route('/api/auth/login', methods=['POST'])
def login():
    global current_session
    data = request.json
    username = data.get('username')
    password = data.get('password')
    refresh_token = data.get('refresh_token')

    logger.info("Login attempt received.")

    try:
        if refresh_token:
            provider_secret = os.getenv('TT_SECRET')
            if not provider_secret:
                return jsonify({"status": "error", "message": "TT_SECRET missing in server env."}), 400
            current_session = Session(provider_secret=provider_secret, refresh_token=refresh_token)
            logger.info("Logged in via Refresh Token.")
        elif username and password:
            current_session = LegacySession(username, password)
            logger.info("Logged in via Username/Password.")
        else:
            return jsonify({"status": "error", "message": "Missing credentials."}), 400

        return jsonify({"status": "connected", "message": "🟢 LOGGED IN"})
    except Exception as e:
        logger.error(f"Login failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 401

@app.route('/api/auth/status')
def get_status():
    session = get_session()
    if session:
        try:
            if session.validate():
                return jsonify({"status": "connected", "message": "🟢 CASINO BRIDGE ACTIVE"})
        except:
            pass
    return jsonify({"status": "disconnected", "message": "🛑 DISCONNECTED"})

@app.route('/api/account/metrics')
def get_metrics():
    logger.info("Fetching account metrics...")
    try:
        session = get_session()
        if not session:
            return jsonify({"error": "Not authenticated. Please login."}), 401

        # Use the session to get accounts
        accounts = Account.get_accounts(session)
        logger.info(f"Accounts fetched. Count: {len(accounts)}")

        if not accounts:
             return jsonify({"error": "No accounts found"}), 404

        acc = accounts[0]
        logger.info(f"Using account: {acc.account_number}")

        balances = acc.get_balances(session)
        positions = acc.get_positions(session)

        net_liq = float(balances.net_liquidating_value)
        used_bp = float(balances.used_derivative_buying_power)
        logger.info(f"Balances: Net Liq={net_liq}, Used BP={used_bp}")

        bp_usage = (used_bp / net_liq) * 100 if net_liq > 0 else 0
        logger.info(f"Calculated BP Usage: {bp_usage}%")

        return jsonify({
            "net_liq": round(net_liq, 2),
            "bp_usage": round(bp_usage, 2),
            "available_bp": round(float(balances.derivative_buying_power), 2),
            "verdict": "🟢 CLEAR" if bp_usage < 30 else "🛑 CEASE TRADING",
            "positions_count": len(positions)
        })
    except TastytradeError as e:
        logger.error(f"Tastytrade API Error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
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
