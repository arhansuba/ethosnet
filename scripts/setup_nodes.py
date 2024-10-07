import asyncio
import aiohttp
import json
import os
import subprocess
import time
from typing import List, Dict, Any
from datetime import datetime

import docker
from prometheus_client import start_http_server, Gauge

class GaiaNetNodeManager:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.client = docker.from_env()
        
        # Prometheus metrics
        self.node_health = Gauge('node_health', 'Health status of GaiaNet nodes', ['node_id'])
        self.node_load = Gauge('node_load', 'Load of GaiaNet nodes', ['node_id'])

    async def setup_nodes(self, node_count: int):
        for i in range(node_count):
            node_id = f"node_{i}"
            config = self._customize_config(i)
            await self._init_node(node_id, config)
            await self._start_node(node_id)
        
        # Start monitoring
        asyncio.create_task(self._monitor_nodes())

    async def _init_node(self, node_id: str, config: Dict[str, Any]):
        node_dir = f"/tmp/gaianet/{node_id}"
        os.makedirs(node_dir, exist_ok=True)
        
        with open(f"{node_dir}/config.json", 'w') as f:
            json.dump(config, f)
        
        subprocess.run(["gaianet", "init", "--config", f"{node_dir}/config.json"], check=True)
        
        self.nodes[node_id] = {
            "status": "initialized",
            "config": config,
            "dir": node_dir,
            "container": None
        }

    async def _start_node(self, node_id: str):
        node = self.nodes[node_id]
        container = self.client.containers.run(
            "gaianet/node:latest",
            command=f"gaianet start --config /gaianet/config.json",
            volumes={node['dir']: {'bind': '/gaianet', 'mode': 'rw'}},
            ports={'8080/tcp': None},
            detach=True
        )
        node['container'] = container
        node['status'] = "running"
        
        # Wait for the node to be ready
        while True:
            try:
                response = await self._make_request(node_id, "/health")
                if response.get('status') == 'ok':
                    break
            except:
                await asyncio.sleep(1)

    async def _stop_node(self, node_id: str):
        node = self.nodes[node_id]
        if node['container']:
            node['container'].stop()
            node['container'].remove()
            node['container'] = None
        node['status'] = "stopped"

    async def _restart_node(self, node_id: str):
        await self._stop_node(node_id)
        await self._start_node(node_id)

    async def _make_request(self, node_id: str, endpoint: str) -> Dict[str, Any]:
        node = self.nodes[node_id]
        port = node['container'].ports['8080/tcp'][0]['HostPort']
        url = f"http://localhost:{port}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.json()

    def _customize_config(self, node_index: int) -> Dict[str, Any]:
        with open(self.config_path, 'r') as f:
            base_config = json.load(f)
        
        # Customize config based on node index
        base_config['node_name'] = f"EthosNet_Node_{node_index}"
        base_config['port'] = 8080 + node_index
        
        return base_config

    async def _monitor_nodes(self):
        while True:
            for node_id, node in self.nodes.items():
                try:
                    health = await self._check_node_health(node_id)
                    load = await self._check_node_load(node_id)
                    
                    self.node_health.labels(node_id=node_id).set(1 if health['status'] == 'ok' else 0)
                    self.node_load.labels(node_id=node_id).set(load['cpu_usage'])
                    
                    if health['status'] != 'ok':
                        print(f"Node {node_id} is unhealthy. Attempting recovery...")
                        await self._recover_node(node_id)
                except Exception as e:
                    print(f"Error monitoring node {node_id}: {str(e)}")
            
            await asyncio.sleep(60)  # Check every minute

    async def _check_node_health(self, node_id: str) -> Dict[str, Any]:
        try:
            return await self._make_request(node_id, "/health")
        except:
            return {"status": "error"}

    async def _check_node_load(self, node_id: str) -> Dict[str, Any]:
        try:
            stats = self.nodes[node_id]['container'].stats(stream=False)
            cpu_usage = stats['cpu_stats']['cpu_usage']['total_usage'] / stats['cpu_stats']['system_cpu_usage'] * 100
            return {"cpu_usage": cpu_usage}
        except:
            return {"cpu_usage": 0}

    async def _recover_node(self, node_id: str):
        try:
            await self._restart_node(node_id)
            print(f"Node {node_id} recovered successfully.")
        except Exception as e:
            print(f"Failed to recover node {node_id}: {str(e)}")

    async def load_balance(self):
        while True:
            node_loads = {}
            for node_id in self.nodes:
                load = await self._check_node_load(node_id)
                node_loads[node_id] = load['cpu_usage']
            
            avg_load = sum(node_loads.values()) / len(node_loads)
            
            for node_id, load in node_loads.items():
                if load > avg_load * 1.2:  # Node is overloaded
                    least_loaded_node = min(node_loads, key=node_loads.get)
                    await self._migrate_workload(node_id, least_loaded_node)
            
            await asyncio.sleep(300)  # Check every 5 minutes

    async def _migrate_workload(self, source_node: str, target_node: str):
        # This is a placeholder for workload migration logic
        # In a real implementation, this would involve moving specific tasks or data
        # between nodes to balance the load
        print(f"Migrating workload from {source_node} to {target_node}")

    async def scale_nodes(self, target_count: int):
        current_count = len(self.nodes)
        if target_count > current_count:
            for i in range(current_count, target_count):
                node_id = f"node_{i}"
                config = self._customize_config(i)
                await self._init_node(node_id, config)
                await self._start_node(node_id)
        elif target_count < current_count:
            nodes_to_remove = list(self.nodes.keys())[target_count:]
            for node_id in nodes_to_remove:
                await self._stop_node(node_id)
                del self.nodes[node_id]

    def start_prometheus_exporter(self, port: int = 8000):
        start_http_server(port)

async def main():
    config_path = "gaianet_base_config.json"
    node_manager = GaiaNetNodeManager(config_path)
    
    # Start Prometheus exporter
    node_manager.start_prometheus_exporter()
    
    # Initial setup
    await node_manager.setup_nodes(3)  # Start with 3 nodes
    
    # Start load balancing task
    asyncio.create_task(node_manager.load_balance())
    
    # Main loop
    while True:
        command = input("Enter command (status/scale/quit): ")
        if command == "status":
            for node_id, node in node_manager.nodes.items():
                print(f"{node_id}: {node['status']}")
        elif command.startswith("scale"):
            try:
                target_count = int(command.split()[1])
                await node_manager.scale_nodes(target_count)
            except:
                print("Invalid scale command. Use 'scale <number>'")
        elif command == "quit":
            break
        else:
            print("Unknown command")

if __name__ == "__main__":
    asyncio.run(main())