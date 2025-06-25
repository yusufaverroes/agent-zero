from python.helpers.api import ApiHandler
from python.helpers.claude_auth import claude_auth_manager
from flask import jsonify


class Handler(ApiHandler):

    def __init__(self, app, lock):
        super().__init__(app, lock)

    async def handle_request(self, request):
        """
        Check Claude Code authentication status.
        
        Returns:
            JSON with authentication status and details
        """
        try:
            auth_info = claude_auth_manager.get_auth_info()
            
            return jsonify({
                "success": True,
                "status": auth_info
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500