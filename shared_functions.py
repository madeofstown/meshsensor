import data_modules

def addNode(iface, nodeID, telemetry, db):
    for n in iface.nodes.values():
        if n["num"] == nodeID:
            newnode = data_modules.Node(nodeID, n["user"]["longName"], n["user"]["shortName"], [telemetry])
            db.nodes.append(newnode)
            break

def processTelemetry(packet, iface, db, db_file = "sensorDB.json"):
    nodeID = int(packet["from"])
    teldata = data_modules.EnvTelemetry(
        time=int(packet["decoded"]["telemetry"]["time"]),
        environmentMetrics=packet["decoded"]["telemetry"]["environmentMetrics"]
    )

    for node in db.nodes:
        if node.nodeID == nodeID:
            node.telemetry.append(teldata)
            break
    else:
        addNode(iface, nodeID, teldata, db)

    db.to_json_file("sensorDB.json", indent=4, ensure_ascii=False)

def requestTelemetry(iface, nodeIDs, channel_index=1):
    for id in nodeIDs:
        iface.sendTelemetry(
            destinationId=id,
            wantResponse=True,
            channelIndex=channel_index,
            telemetryType="environment_metrics"
        )