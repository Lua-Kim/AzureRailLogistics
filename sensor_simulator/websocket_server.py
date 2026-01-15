# sensor_simulator/websocket_server.py
import asyncio
import websockets
import json

class WebSocketServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        self.data_queue = asyncio.Queue()

    async def _register(self, websocket):
        """새로운 클라이언트 연결을 등록합니다."""
        self.clients.add(websocket)
        print(f"New client connected: {websocket.remote_address}. Total clients: {len(self.clients)}")
        try:
            await websocket.wait_closed()
        finally:
            self._unregister(websocket)

    async def _unregister(self, websocket):
        """클라이언트 연결 해제를 처리합니다."""
        self.clients.remove(websocket)
        print(f"Client disconnected: {websocket.remote_address}. Total clients: {len(self.clients)}")

    async def _broadcast_messages(self):
        """큐에 있는 데이터를 모든 클라이언트에게 브로드캐스트합니다."""
        while True:
            data = await self.data_queue.get()
            if self.clients:
                # 데이터를 JSON 문자열로 변환
                message = json.dumps(data)
                # 모든 클라이언트에게 전송
                await asyncio.wait([client.send(message) for client in self.clients])

    async def start(self):
        """웹소켓 서버를 시작합니다."""
        print(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        self.server = await websockets.serve(self._register, self.host, self.port)
        # 백그라운드에서 메시지 브로드캐스트 작업 실행
        asyncio.create_task(self._broadcast_messages())

    async def stop(self):
        """웹소켓 서버를 중지합니다."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            print("WebSocket server stopped.")

    def send_data(self, data):
        """외부에서 데이터를 받아 큐에 넣습니다."""
        self.data_queue.put_nowait(data)

# 이 파일이 직접 실행될 경우를 위한 테스트 로직
if __name__ == '__main__':
    async def main():
        ws_server = WebSocketServer('localhost', 8765)
        await ws_server.start()
        
        # 3초마다 테스트 데이터 전송
        counter = 0
        while True:
            test_data = {'message': f'Test data {counter}', 'timestamp': asyncio.get_event_loop().time()}
            ws_server.send_data(test_data)
            counter += 1
            await asyncio.sleep(3)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Test server stopped.")
