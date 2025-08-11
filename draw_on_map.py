from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsGeometry, QgsRectangle, QgsWkbTypes
from PyQt5.QtCore import pyqtSignal, Qt, QObject
from PyQt5.QtGui import QColor
from qgis.utils import iface

class StartDrawOnMap(QgsMapTool):
    rectangleCreated = pyqtSignal(QgsGeometry)

    def __init__(self, canvas):
        super(StartDrawOnMap, self).__init__(canvas)  # Pass canvas to QgsMapTool
        self.canvas = canvas
        self.start_point = None
        self.end_point = None
        self.rubber_band = QgsRubberBand(canvas, QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setColor(QColor(255, 0, 0, 100))
        self.rubber_band.setFillColor(QColor(255, 0, 0, 40))
        self.rubber_band.setWidth(2)
        self.rubber_band.setVisible(False)

    def canvasPressEvent(self, event):
        self.start_point = self.toMapCoordinates(event.pos())
        self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)
        self.rubber_band.setVisible(True)

    def canvasMoveEvent(self, event):
        if not self.start_point:
            return
        current_point = self.toMapCoordinates(event.pos())
        rect = QgsRectangle(self.start_point, current_point)
        geom = QgsGeometry.fromRect(rect)
        self.rubber_band.setToGeometry(geom, None)

    def canvasReleaseEvent(self, event):
        self.end_point = self.toMapCoordinates(event.pos())
        if self.start_point and self.end_point:
            rect = QgsRectangle(self.start_point, self.end_point)
            geom = QgsGeometry.fromRect(rect)
            self.rectangleCreated.emit(geom)
            self.rubber_band.reset(QgsWkbTypes.PolygonGeometry)  # 👈 This clears the square
        self.canvas.unsetMapTool(self)
        
class DrawOnMap:
    def __init__(self, iface, min_x_input, max_x_input, min_y_input, max_y_input, dialog):
        self.canvas = iface.mapCanvas()
        self.min_x_input = min_x_input
        self.max_x_input = max_x_input
        self.min_y_input = min_y_input
        self.max_y_input = max_y_input
        self.dialog = dialog

    def activate_draw_extent(self):
        self.tool = StartDrawOnMap(self.canvas)
        self.dialog.hide()  # hide before drawing

        def on_rectangle_drawn(geom: QgsGeometry):
            extent = geom.boundingBox()
            self.min_x_input.setText(str(extent.xMinimum()))
            self.max_x_input.setText(str(extent.xMaximum()))
            self.min_y_input.setText(str(extent.yMinimum()))
            self.max_y_input.setText(str(extent.yMaximum()))
            self.dialog.show()  # show again after setting values

        self.tool.rectangleCreated.connect(on_rectangle_drawn)
        self.canvas.setMapTool(self.tool)

