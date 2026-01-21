import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class IncidenteConsumer(AsyncWebsocketConsumer):


    async def connect(self):

        user = self.scope["user"]

        if not user or user.is_anonymous:
            await self.close()
            return

        role = await self.get_user_role(user)

        if not role:
            await self.close()
            return

        self.role = role
        self.group_name = f"rol_{self.role}"

        # grupo por rol
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        # 🔥 grupo catalogos
        await self.channel_layer.group_add(
            "catalogos",
            self.channel_name
        )

        await self.accept()



    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

        await self.channel_layer.group_discard(
            "catalogos",
            self.channel_name
        )



    async def enviar_evento(self, event):
        await self.send(text_data=json.dumps(event["data"]))


    # ----------- helpers -----------

    @database_sync_to_async
    def get_user_role(self, user):
        try:
            return user.perfil.rol
        except:
            return None
