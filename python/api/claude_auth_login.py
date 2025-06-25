from python.helpers.api import ApiHandler
from python.helpers.claude_auth import claude_auth_manager
from flask import jsonify


class Handler(ApiHandler):

    def __init__(self, app, lock):
        super().__init__(app, lock)

    async def handle_request(self, request):
        """
        Initiate Claude Code Pro/Max login process.
        
        Returns:
            JSON with login result
        """
        try:
            success, message = await claude_auth_manager.initiate_login()
            
            return jsonify({
                "success": success,
                "message": message
            })
            
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500