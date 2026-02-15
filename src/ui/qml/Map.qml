import QtQuick
import QtLocation
import QtPositioning
import QtQuick.Controls
import Qt.labs.platform

Item {
    width: 800
    height: 600

    Plugin {
        id: mapPlugin
        name: "osm"

        PluginParameter {
            name: "osm.useragent"
            value: "ARDFEvent/1.0"
        }

        PluginParameter {
            name: "osm.mapping.custom.host"
            value: "https://tile.opentopomap.org/"
        }
    }

    Map {
        id: map
        objectName: "map"
        anchors.fill: parent
        plugin: mapPlugin
        center: QtPositioning.coordinate(50.84053, 15.10577)
        zoomLevel: 14

        activeMapType: {
            for (let i = 0; i < supportedMapTypes.length; i++) {
                if (supportedMapTypes[i].style === MapType.CustomMap) {
                    return supportedMapTypes[i];
                }
            }
            return supportedMapTypes[supportedMapTypes.length - 1];
        }

        DragHandler {
            id: dragHandler
            target: null
            onTranslationChanged: delta => map.pan(-delta.x, -delta.y)
        }

        WheelHandler {
            id: wheelHandler
            target: map
            acceptedDevices: PointerDevice.AllDevices
            onWheel: event => {
                const step = 0.05;
                if (event.angleDelta.y > 0)
                    map.zoomLevel = Math.min(24, map.zoomLevel + step);
                else
                    map.zoomLevel = Math.max(1, map.zoomLevel - step);
                event.accepted = true;
            }
        }

        TapHandler {
            onTapped: (point) => {
                var scenePoint = point.position;
                var coord = map.toCoordinate(scenePoint);

                mapHandler.handle_click(coord.latitude, coord.longitude);
            }
        }

        Connections {
            target: mapHandler

            function onControlsChange(jsonStr) {
                Qt.callLater(() => {
                    map.setPoints(jsonStr);
                });
            }

            function onRemovePaths() {
                Qt.callLater(() => {
                    pathsModel.clear();
                });
            }

            function onAddPath(jsonStr) {
                Qt.callLater(() => {
                    map.addPath(jsonStr);
                });
            }
        }

        ListModel {
            id: mapsModel
        }

        function addMap(geoData) {
            mapsModel.append(JSON.parse(geoData));
        }

        MapItemView {
            model: mapsModel
            delegate: MapQuickItem {
                id: imageOverlay
                coordinate: QtPositioning.coordinate(topLeftLat, topLeftLon)
                anchorPoint: Qt.point(0, 0)
                z: 10
                sourceItem: Image {
                    id: overlayImage

                    source: imagePath
                    opacity: 0.8
                    smooth: true
                    fillMode: Image.Stretch

                    width: {
                        var metersPerPixel = 40075016.68 / Math.pow(2, map.zoomLevel + 8);
                        return widthMeters / metersPerPixel;
                    }

                    height: {
                        var metersPerPixel = 40075016.68 / Math.pow(2, map.zoomLevel + 8);
                        return heightMeters / metersPerPixel;
                    }
                }
            }
        }

        ListModel {
            id: pointsModel
        }

        function setPoints(pointsJson) {
            if (!pointsJson) {
                pointsModel.clear();
                return;
            }

            var points = JSON.parse(pointsJson);

            var pointsArray = points.arr;

            var sumLat = 0;
            var sumLon = 0;
            var count = 0;

            pointsModel.clear();
            for (var i = 0; i < pointsArray.length; i++) {
                var p = pointsArray[i];
                pointsModel.append(p);
                sumLat += p.latitude;
                sumLon += p.longitude;
                count += 1;
            }

            if (points.center && count > 0) {
                map.center = QtPositioning.coordinate(sumLat / count, sumLon / count);
            }
        }

        function clearPoints() {
            pointsModel.clear();
        }

        MapItemView {
            model: pointsModel
            delegate: MapItemGroup {
                id: coursePoint
                readonly property var pos: QtPositioning.coordinate(latitude, longitude)
                readonly property var cId: control_id

                MapQuickItem {
                    coordinate: pos
                    anchorPoint: Qt.point(30, 30)
                    z: 100

                    sourceItem: Item {
                        width: 60
                        height: 60

                        TapHandler {
                            onDoubleTapped: {
                                mapHandler.control_dblclicked(coursePoint.cId.toString());
                            }
                        }

                        DragHandler {
                            id: pointDragHandler
                            target: null

                            cursorShape: active ? Qt.BlankCursor : Qt.ArrowCursor

                            grabPermissions: PointerHandler.ApprovesTakeOverByHandlers | PointerHandler.CanTakeOverFromHandlers | PointerHandler.CanTakeOverFromItems

                            onActiveChanged: {
                                if (!active) {
                                    mapHandler.control_moved(coursePoint.cId.toString(), coursePoint.pos.latitude, coursePoint.pos.longitude);
                                }
                            }

                            onCentroidChanged: {
                                if (active) {
                                    var scenePos = centroid.scenePosition;
                                    var newCoord = map.toCoordinate(scenePos);

                                    if (newCoord.isValid) {
                                        pointsModel.setProperty(index, "latitude", newCoord.latitude);
                                        pointsModel.setProperty(index, "longitude", newCoord.longitude);
                                    }
                                }
                            }
                        }
                    }
                }

                MapItemGroup {
                    id: pointGraphics

                    MapCircle {
                        id: center
                        visible: pointDragHandler.active
                        center: pos
                        radius: 3
                        color: active ? "#ff00ff" : "#ff0000"
                        border.width: 0
                    }

                    MapCircle {
                        id: circle
                        visible: (type === "control" && pointDragHandler.active) || type === "start"
                        center: pos
                        radius: type === "start" ? mapHandler.start_circle : mapHandler.control_circle
                        border.width: 2
                        border.color: active ? "#ff00ff" : "#ff0000"
                        color: "transparent"
                    }

                    MapPolygon {
                        id: start
                        visible: type === "start"
                        border.width: 3
                        border.color: active ? "#ff00ff" : "#ff0000"
                        color: "transparent"
                        path: [pos.atDistanceAndAzimuth(45, 0), pos.atDistanceAndAzimuth(45, 120), pos.atDistanceAndAzimuth(45, 240)]
                    }

                    MapCircle {
                        id: control
                        visible: type === "control" || type === "finish"
                        center: pos
                        radius: 30
                        border.width: 3
                        border.color: active ? "#ff00ff" : "#ff0000"
                        color: "transparent"
                    }

                    MapCircle {
                        id: finish
                        visible: type === "finish"
                        center: pos
                        radius: 20
                        border.width: 3
                        border.color: active ? "#ff00ff" : "#ff0000"
                        color: "transparent"
                    }

                    MapQuickItem {
                        id: labelItem
                        coordinate: pos.atDistanceAndAzimuth(30, 45)
                        anchorPoint: Qt.point(0, labelElem.height)

                        zoomLevel: 15

                        sourceItem: Text {
                            id: labelElem
                            font.pixelSize: 18
                            font.family: "Arial"
                            text: label
                            color: active ? "#ff00ff" : "#ff0000"
                        }
                    }
                }
            }
        }

        ListModel {
            id: pathsModel
        }

        function trimPath(originalPath, distanceMeters) {
            if (originalPath.length < 2) return originalPath;

            let newPath = [...originalPath];

            let start = newPath[0];
            let end = newPath[1];
            let bearingStart = start.azimuthTo(end);
            newPath[0] = start.atDistanceAndAzimuth(distanceMeters, bearingStart);

            let bearingEnd = end.azimuthTo(start);
            newPath[1] = end.atDistanceAndAzimuth(distanceMeters, bearingEnd);

            return newPath;
        }

        function addPath(pathJson) {
            var pathData = JSON.parse(pathJson);
            var pathCoords = pathData.map(p => QtPositioning.coordinate(p.lat, p.lon));
            var trimmed = trimPath(pathCoords, 40);
            let cleanArray = [];
            for (let p of trimmed) {
                cleanArray.push(p);
            }
            pathsModel.append({path: cleanArray});
        }

        MapItemView {
            model: pathsModel
            delegate: MapPolyline {
                line.width: 3
                line.color: "#ff00ff"

                path: {
                    let temp = [];
                    let nestedModel = model.path;

                    if (nestedModel && nestedModel.count > 0) {
                        for (var i = 0; i < nestedModel.count; i++) {
                            let item = nestedModel.get(i);
                            temp.push(QtPositioning.coordinate(item.latitude, item.longitude));
                        }
                    }
                    return temp;
                }
            }
        }
    }
}
