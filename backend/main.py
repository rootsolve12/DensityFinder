"""ForestMesh API. Single shared demo scenario; SQLite event audit trail."""
import asyncio
import json
import os
import sqlite3
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from backend.engine import Simulation, Scenario

app=FastAPI(title='ForestMesh API',version='0.1.0')
sim=Simulation()
DB=os.environ.get('FORESTMESH_DB','forestmesh.sqlite3')

def persist(event):
    with sqlite3.connect(DB) as c:
        c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)')
        c.execute('INSERT INTO events(payload) VALUES (?)',(json.dumps(event),))

@app.get('/api/health')
def health(): return {'status':'ok','mode':'simulation'}
@app.get('/api/state')
def state(): return sim.snapshot()
@app.post('/api/scenario')
def scenario(config:Scenario):
    global sim
    sim=Simulation(config)
    return sim.snapshot()
@app.post('/api/nodes/{node_id}/toggle')
def toggle(node_id:int):
    if not 0<=node_id<len(sim.nodes): raise HTTPException(404,'Unknown sensor')
    sim.nodes[node_id]['active']=not sim.nodes[node_id]['active']
    return sim.snapshot()
class EventRequest(BaseModel):
    node: int | None = Field(None,ge=0)
@app.post('/api/events')
def event(body:EventRequest):
    if body.node is not None and body.node>=len(sim.nodes): raise HTTPException(404,'Unknown sensor')
    persist(sim.event(body.node))
    return sim.snapshot()
@app.get('/api/events/history')
def history():
    with sqlite3.connect(DB) as c:
        c.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)')
        return [json.loads(r[0]) for r in c.execute('SELECT payload FROM events ORDER BY id DESC LIMIT 100')]
@app.post('/api/optimize')
def optimize():
    sim.optimize()
    return sim.snapshot()
@app.websocket('/ws')
async def websocket(ws:WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json(sim.snapshot())
            await asyncio.sleep(2)
    except (WebSocketDisconnect,RuntimeError): pass

build=Path(__file__).resolve().parents[1]/'frontend'/'dist'
if build.exists(): app.mount('/',StaticFiles(directory=build,html=True),name='dashboard')
