from fastapi.testclient import TestClient
from backend import main

def test_end_to_end(tmp_path,monkeypatch):
    monkeypatch.setattr(main,'DB',str(tmp_path/'events.sqlite3'))
    with TestClient(main.app) as client:
        assert client.get('/api/health').json()['status']=='ok'
        s=client.post('/api/scenario',json={'count':50,'seed':42,'range':250}).json()
        assert len(s['nodes'])==50
        assert client.post('/api/scenario',json={'count':500}).status_code==422
        event=client.post('/api/events',json={'node':10}).json()['events'][0]
        assert event['node']==10
        assert len(client.get('/api/events/history').json())==1
        failed=client.post('/api/nodes/0/toggle').json()
        assert failed['metrics']['reachable']==0
        assert not client.post('/api/events',json={'node':10}).json()['events'][0]['delivered']
        client.post('/api/nodes/0/toggle')
        assert client.post('/api/optimize').json()['comparison'] is not None
        assert client.post('/api/events',json={'node':999}).status_code==404
        assert client.post('/api/nodes/999/toggle').status_code==404
        with client.websocket_connect('/ws') as ws:
            assert len(ws.receive_json()['nodes'])==50
