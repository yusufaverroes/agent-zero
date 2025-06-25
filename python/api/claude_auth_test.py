from python.helpers.api import ApiHandler
from python.helpers.claude_auth import claude_auth_manager
from flask import jsonify


class Handler(ApiHandler):

    def __init__(self, app, lock):
        super().__init__(app, lock)

    async def handle_request(self, request):
        """
        Test Claude Code connection.
        
        Returns:
            JSON with connection test result
        """
        try:
            success, message = await claude_auth_manager.test_claude_connection()
            
            return jsonify({
                "success": success,
                "message": message
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500