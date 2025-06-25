from python.helpers.api import ApiHandler
from python.helpers.claude_auth import claude_auth_manager
from flask import jsonify


class Handler(ApiHandler):

    def __init__(self, app, lock):
        super().__init__(app, lock)

    async def handle_request(self, request):
        """
        Logout from Claude Code and clear credentials.
        
        Returns:
            JSON with logout result
        """
        try:
            success, message = claude_auth_manager.logout()
            
            return jsonify({
                "success": success,
                "message": message
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500