import React, { useState, useRef, useEffect } from 'react';

export default function LaserControlApp() {
  // State for canvas drawing
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [shapes, setShapes] = useState([]);
  const [selectedShape, setSelectedShape] = useState(null);
  
  // State for file operations
  const [fileName, setFileName] = useState('بدون نام');
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // DXF import/export settings
  const [dxfScale, setDxfScale] = useState(1.0);
  const [showDxfSettings, setShowDxfSettings] = useState(false);
  const [dxfImportInProgress, setDxfImportInProgress] = useState(false);
  
  // State for laser settings
  const [laserPower, setLaserPower] = useState(50);
  const [laserSpeed, setLaserSpeed] = useState(100);
  const [workspaceWidth, setWorkspaceWidth] = useState(1300);
  const [workspaceHeight, setWorkspaceHeight] = useState(900);
  
  // State for layers
  const [layers, setLayers] = useState([
    { id: 1, name: 'Layer 1', color: '#FF0000', power: 50, speed: 100, mode: 'cut' },
    { id: 2, name: 'Layer 2', color: '#0000FF', power: 30, speed: 200, mode: 'engrave' }
  ]);
  const [selectedLayer, setSelectedLayer] = useState(1);

  // Tool selection
  const [currentTool, setCurrentTool] = useState('select');
  
  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw grid
    drawGrid(ctx, canvas.width, canvas.height);
    
    // Draw all shapes
    shapes.forEach((shape, index) => {
      ctx.beginPath();
      
      // Set color based on the layer
      const layer = layers.find(l => l.id === shape.layerId);
      ctx.strokeStyle = layer ? layer.color : '#000000';
      
      if (shape.type === 'rect') {
        ctx.rect(shape.x, shape.y, shape.width, shape.height);
      } else if (shape.type === 'line') {
        ctx.moveTo(shape.startX, shape.startY);
        ctx.lineTo(shape.endX, shape.endY);
      } else if (shape.type === 'circle') {
        ctx.arc(shape.x, shape.y, shape.radius, 0, Math.PI * 2);
      }
      
      ctx.stroke();
      
      // Highlight selected shape
      if (selectedShape === index) {
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = '#00FF00';
        if (shape.type === 'rect') {
          ctx.strokeRect(shape.x - 2, shape.y - 2, shape.width + 4, shape.height + 4);
        } else if (shape.type === 'line') {
          ctx.beginPath();
          ctx.moveTo(shape.startX, shape.startY);
          ctx.lineTo(shape.endX, shape.endY);
          ctx.stroke();
        } else if (shape.type === 'circle') {
          ctx.beginPath();
          ctx.arc(shape.x, shape.y, shape.radius + 2, 0, Math.PI * 2);
          ctx.stroke();
        }
        ctx.setLineDash([]);
      }
    });
    
  }, [shapes, selectedShape, layers]);
  
  const drawGrid = (ctx, width, height) => {
    ctx.strokeStyle = '#DDDDDD';
    ctx.lineWidth = 0.5;
    
    // Draw vertical lines
    for (let x = 20; x < width; x += 20) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    
    // Draw horizontal lines
    for (let y = 20; y < height; y += 20) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // Draw ruler
    ctx.fillStyle = '#000000';
    ctx.font = '10px Arial';
    for (let x = 0; x < width; x += 100) {
      ctx.fillText(x.toString(), x + 2, 10);
    }
    for (let y = 0; y < height; y += 100) {
      ctx.fillText(y.toString(), 2, y + 10);
    }
  };
  
  const handleMouseDown = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentTool === 'select') {
      // Check if clicking on an existing shape
      for (let i = shapes.length - 1; i >= 0; i--) {
        const shape = shapes[i];
        if (isPointInShape(x, y, shape)) {
          setSelectedShape(i);
          return;
        }
      }
      setSelectedShape(null);
    } else {
      setDrawing(true);
      setPosition({ x, y });
      
      if (currentTool === 'rect') {
        const newRect = {
          type: 'rect',
          x: x,
          y: y,
          width: 0,
          height: 0,
          layerId: selectedLayer
        };
        setShapes([...shapes, newRect]);
        setSelectedShape(shapes.length);
      } else if (currentTool === 'line') {
        const newLine = {
          type: 'line',
          startX: x,
          startY: y,
          endX: x,
          endY: y,
          layerId: selectedLayer
        };
        setShapes([...shapes, newLine]);
        setSelectedShape(shapes.length);
      } else if (currentTool === 'circle') {
        const newCircle = {
          type: 'circle',
          x: x,
          y: y,
          radius: 0,
          layerId: selectedLayer
        };
        setShapes([...shapes, newCircle]);
        setSelectedShape(shapes.length);
      }
    }
  };
  
  const handleMouseMove = (e) => {
    if (!drawing) return;
    
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const newShapes = [...shapes];
    const currentShape = newShapes[newShapes.length - 1];
    
    if (currentTool === 'rect') {
      currentShape.width = x - currentShape.x;
      currentShape.height = y - currentShape.y;
    } else if (currentTool === 'line') {
      currentShape.endX = x;
      currentShape.endY = y;
    } else if (currentTool === 'circle') {
      const dx = x - currentShape.x;
      const dy = y - currentShape.y;
      currentShape.radius = Math.sqrt(dx * dx + dy * dy);
    }
    
    setShapes(newShapes);
  };
  
  const handleMouseUp = () => {
    setDrawing(false);
  };
  
  const isPointInShape = (x, y, shape) => {
    if (shape.type === 'rect') {
      return x >= shape.x && x <= shape.x + shape.width && 
             y >= shape.y && y <= shape.y + shape.height;
    } else if (shape.type === 'line') {
      // Check if point is close to the line
      const A = { x: shape.startX, y: shape.startY };
      const B = { x: shape.endX, y: shape.endY };
      const distance = pointToLineDistance(x, y, A, B);
      return distance < 5; // 5px threshold
    } else if (shape.type === 'circle') {
      const dx = x - shape.x;
      const dy = y - shape.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      return Math.abs(distance - shape.radius) < 5; // 5px threshold
    }
    return false;
  };
  
  const pointToLineDistance = (x, y, A, B) => {
    const numerator = Math.abs((B.y - A.y) * x - (B.x - A.x) * y + B.x * A.y - B.y * A.x);
    const denominator = Math.sqrt(Math.pow(B.y - A.y, 2) + Math.pow(B.x - A.x, 2));
    return numerator / denominator;
  };
  
  const handleLayerSelect = (id) => {
    setSelectedLayer(id);
  };
  
  const handleLayerPropertyChange = (id, property, value) => {
    const newLayers = layers.map(layer => {
      if (layer.id === id) {
        return { ...layer, [property]: value };
      }
      return layer;
    });
    setLayers(newLayers);
  };
  
  const addNewLayer = () => {
    const newId = Math.max(...layers.map(l => l.id)) + 1;
    setLayers([
      ...layers, 
      { 
        id: newId, 
        name: `Layer ${newId}`, 
        color: getRandomColor(),
        power: 50,
        speed: 100,
        mode: 'cut'
      }
    ]);
  };
  
  const getRandomColor = () => {
    return '#' + Math.floor(Math.random()*16777215).toString(16);
  };
  
  const deleteLayer = (id) => {
    if (layers.length <= 1) return;
    setLayers(layers.filter(layer => layer.id !== id));
    if (selectedLayer === id) {
      setSelectedLayer(layers[0].id);
    }
  };
  
  const deleteSelectedShape = () => {
    if (selectedShape === null) return;
    const newShapes = [...shapes];
    newShapes.splice(selectedShape, 1);
    setShapes(newShapes);
    setSelectedShape(null);
  };
  
  const importDXF = () => {
    setShowDxfSettings(true);
  };
  
  const startDXFImport = () => {
    // Create an input element
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '.dxf';
    
    fileInput.onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      setFileName(file.name.replace('.dxf', ''));
      setDxfImportInProgress(true);
      
      const reader = new FileReader();
      reader.onload = (event) => {
        const dxfContent = event.target.result;
        parseDXF(dxfContent);
        setDxfImportInProgress(false);
      };
      
      reader.readAsText(file);
    };
    
    fileInput.click();
    setShowDxfSettings(false);
  };
  
  const parseDXF = (content) => {
    // Simple DXF parser implementation
    try {
      // Reset shapes or keep them based on user preference
      const keepExistingShapes = window.confirm('آیا می‌خواهید اشکال موجود را حفظ کنید؟');
      const newShapes = keepExistingShapes ? [...shapes] : [];
      
      // Simple parsing logic for DXF format
      const lines = content.split('\n');
      let currentEntity = null;
      let readingEntity = false;
      let entityType = null;
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        
        // Start of an entity
        if (line === '0' && lines[i+1] && lines[i+1].trim() === 'ENTITY') {
          readingEntity = true;
          currentEntity = {};
          i++; // Skip ENTITY line
          continue;
        }
        
        // End of an entity
        if (readingEntity && line === '0' && lines[i+1] && lines[i+1].trim() !== 'ENTITY') {
          readingEntity = false;
          
          // Process the entity we've read
          if (entityType === 'LINE') {
            newShapes.push({
              type: 'line',
              startX: parseFloat(currentEntity.x1 || 0) * dxfScale,
              startY: parseFloat(currentEntity.y1 || 0) * dxfScale,
              endX: parseFloat(currentEntity.x2 || 0) * dxfScale,
              endY: parseFloat(currentEntity.y2 || 0) * dxfScale,
              layerId: selectedLayer
            });
          } else if (entityType === 'CIRCLE') {
            newShapes.push({
              type: 'circle',
              x: parseFloat(currentEntity.x || 0) * dxfScale,
              y: parseFloat(currentEntity.y || 0) * dxfScale,
              radius: parseFloat(currentEntity.radius || 0) * dxfScale,
              layerId: selectedLayer
            });
          } else if (entityType === 'LWPOLYLINE' || entityType === 'POLYLINE') {
            // For simplicity, we'll convert polylines to individual line segments
            if (currentEntity.vertices && currentEntity.vertices.length > 1) {
              for (let j = 0; j < currentEntity.vertices.length - 1; j++) {
                newShapes.push({
                  type: 'line',
                  startX: currentEntity.vertices[j].x * dxfScale,
                  startY: currentEntity.vertices[j].y * dxfScale,
                  endX: currentEntity.vertices[j+1].x * dxfScale,
                  endY: currentEntity.vertices[j+1].y * dxfScale,
                  layerId: selectedLayer
                });
              }
              
              // Close the polyline if it's closed
              if (currentEntity.closed && currentEntity.vertices.length > 2) {
                newShapes.push({
                  type: 'line',
                  startX: currentEntity.vertices[currentEntity.vertices.length-1].x * dxfScale,
                  startY: currentEntity.vertices[currentEntity.vertices.length-1].y * dxfScale,
                  endX: currentEntity.vertices[0].x * dxfScale,
                  endY: currentEntity.vertices[0].y * dxfScale,
                  layerId: selectedLayer
                });
              }
            }
          } else if (entityType === 'ARC') {
            // Convert arc to a series of lines
            // This is a simplified approach
            const center = { 
              x: parseFloat(currentEntity.x || 0) * dxfScale, 
              y: parseFloat(currentEntity.y || 0) * dxfScale 
            };
            const radius = parseFloat(currentEntity.radius || 0) * dxfScale;
            const startAngle = parseFloat(currentEntity.startAngle || 0) * Math.PI / 180;
            const endAngle = parseFloat(currentEntity.endAngle || 0) * Math.PI / 180;
            
            // Generate points along the arc
            const segments = 20; // Number of segments to approximate the arc
            const angleStep = (endAngle - startAngle) / segments;
            
            let points = [];
            for (let j = 0; j <= segments; j++) {
              const angle = startAngle + j * angleStep;
              const x = center.x + radius * Math.cos(angle);
              const y = center.y + radius * Math.sin(angle);
              points.push({ x, y });
            }
            
            // Create lines between points
            for (let j = 0; j < points.length - 1; j++) {
              newShapes.push({
                type: 'line',
                startX: points[j].x,
                startY: points[j].y,
                endX: points[j+1].x,
                endY: points[j+1].y,
                layerId: selectedLayer
              });
            }
          } else if (entityType === 'RECTANGLE' || entityType === 'LWPOLYLINE' && currentEntity.vertices && currentEntity.vertices.length === 4) {
            // Handle rectangles (often represented as closed polylines with 4 vertices)
            // Convert to our internal rectangle representation
            const vertices = currentEntity.vertices;
            if (vertices) {
              // Find min and max X and Y to create the rectangle
              const xValues = vertices.map(v => v.x * dxfScale);
              const yValues = vertices.map(v => v.y * dxfScale);
              
              const minX = Math.min(...xValues);
              const maxX = Math.max(...xValues);
              const minY = Math.min(...yValues);
              const maxY = Math.max(...yValues);
              
              newShapes.push({
                type: 'rect',
                x: minX,
                y: minY,
                width: maxX - minX,
                height: maxY - minY,
                layerId: selectedLayer
              });
            }
          }
          
          entityType = null;
          currentEntity = null;
          continue;
        }
        
        // Reading entity type
        if (readingEntity && line === '0' && i+1 < lines.length) {
          entityType = lines[i+1].trim();
          i++; // Skip entity type line
          continue;
        }
        
        // Reading entity data
        if (readingEntity && entityType) {
          // Parse according to entity type
          if (entityType === 'LINE') {
            if (line === '10' && i+1 < lines.length) {
              currentEntity.x1 = lines[i+1].trim();
              i++;
            } else if (line === '20' && i+1 < lines.length) {
              currentEntity.y1 = lines[i+1].trim();
              i++;
            } else if (line === '11' && i+1 < lines.length) {
              currentEntity.x2 = lines[i+1].trim();
              i++;
            } else if (line === '21' && i+1 < lines.length) {
              currentEntity.y2 = lines[i+1].trim();
              i++;
            }
          } else if (entityType === 'CIRCLE') {
            if (line === '10' && i+1 < lines.length) {
              currentEntity.x = lines[i+1].trim();
              i++;
            } else if (line === '20' && i+1 < lines.length) {
              currentEntity.y = lines[i+1].trim();
              i++;
            } else if (line === '40' && i+1 < lines.length) {
              currentEntity.radius = lines[i+1].trim();
              i++;
            }
          } else if (entityType === 'ARC') {
            if (line === '10' && i+1 < lines.length) {
              currentEntity.x = lines[i+1].trim();
              i++;
            } else if (line === '20' && i+1 < lines.length) {
              currentEntity.y = lines[i+1].trim();
              i++;
            } else if (line === '40' && i+1 < lines.length) {
              currentEntity.radius = lines[i+1].trim();
              i++;
            } else if (line === '50' && i+1 < lines.length) {
              currentEntity.startAngle = lines[i+1].trim();
              i++;
            } else if (line === '51' && i+1 < lines.length) {
              currentEntity.endAngle = lines[i+1].trim();
              i++;
            }
          } else if (entityType === 'LWPOLYLINE' || entityType === 'POLYLINE') {
            // Polylines are more complex, for simplicity we'll just collect vertices
            if (!currentEntity.vertices) {
              currentEntity.vertices = [];
              currentEntity.closed = false;
            }
            
            // Check for closed flag
            if (line === '70' && i+1 < lines.length && parseInt(lines[i+1].trim()) === 1) {
              currentEntity.closed = true;
              i++;
            }
            
            // Read vertex coordinates
            if (line === '10' && i+1 < lines.length) {
              const x = parseFloat(lines[i+1].trim());
              i++;
              
              // Look ahead for Y coordinate
              if (i+2 < lines.length && lines[i+1].trim() === '20') {
                i++;
                const y = parseFloat(lines[i+1].trim());
                i++;
                
                currentEntity.vertices.push({ x, y });
              }
            }
          }
        }
      }
      
      // Update shapes with the parsed data
      setShapes(newShapes);
      setHasUnsavedChanges(true);
      
      // Show results
      alert(`فایل DXF با موفقیت وارد شد. ${keepExistingShapes ? (newShapes.length - shapes.length) : newShapes.length} شکل جدید اضافه شد.`);
      
    } catch (error) {
      console.error('Error parsing DXF file:', error);
      alert('خطا در خواندن فایل DXF. لطفاً از صحت فرمت فایل مطمئن شوید.');
    }
  };
  
  const startLaserJob = () => {
    alert('In a real application, this would send the job to the laser machine with the current settings');
  };
  
  return (
    <div className="flex flex-col h-screen bg-gray-100">
      {/* Top Toolbar */}
      <div className="bg-gray-800 text-white p-2">
        <div className="flex justify-between items-center">
          <div className="text-xl font-bold">لیزر کنترل - نسخه 1.0</div>
          <div className="flex space-x-4">
            <button className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded flex items-center" onClick={importDXF}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
              </svg>
              وارد کردن DXF
            </button>
            <button className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded flex items-center" onClick={startLaserJob}>
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              شروع کار لیزر
            </button>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Tools */}
        <div className="w-16 bg-gray-700 text-white p-2">
          <div className="flex flex-col space-y-4">
            <button 
              className={`p-2 rounded ${currentTool === 'select' ? 'bg-blue-600' : 'bg-gray-600'}`}
              onClick={() => setCurrentTool('select')}
              title="انتخاب"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 15l-5-5 5-5" />
              </svg>
            </button>
            <button 
              className={`p-2 rounded ${currentTool === 'rect' ? 'bg-blue-600' : 'bg-gray-600'}`}
              onClick={() => setCurrentTool('rect')}
              title="مستطیل"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
            </button>
            <button 
              className={`p-2 rounded ${currentTool === 'line' ? 'bg-blue-600' : 'bg-gray-600'}`}
              onClick={() => setCurrentTool('line')}
              title="خط"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 12h16" />
              </svg>
            </button>
            <button 
              className={`p-2 rounded ${currentTool === 'circle' ? 'bg-blue-600' : 'bg-gray-600'}`}
              onClick={() => setCurrentTool('circle')}
              title="دایره"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
            <button 
              className="p-2 rounded bg-red-600"
              onClick={deleteSelectedShape}
              title="حذف"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
        
        {/* Main Canvas Area */}
        <div className="flex-1 overflow-auto bg-white border border-gray-300">
          <canvas 
            ref={canvasRef}
            width={workspaceWidth} 
            height={workspaceHeight}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            className="bg-white"
          />
        </div>
        
        {/* Right Sidebar - Layers & Properties */}
        <div className="w-64 bg-gray-200 overflow-y-auto p-2">
          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h3 className="font-bold">لایه‌ها</h3>
              <button 
                className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-sm"
                onClick={addNewLayer}
              >
                +
              </button>
            </div>
            {layers.map(layer => (
              <div 
                key={layer.id} 
                className={`p-2 mb-1 rounded cursor-pointer flex justify-between items-center ${selectedLayer === layer.id ? 'bg-blue-100 border border-blue-500' : 'bg-white border border-gray-300'}`}
                onClick={() => handleLayerSelect(layer.id)}
              >
                <div className="flex items-center">
                  <div 
                    className="w-4 h-4 mr-2 rounded-full" 
                    style={{ backgroundColor: layer.color }}
                  />
                  <span>{layer.name}</span>
                </div>
                <button 
                  className="text-red-600 hover:text-red-800"
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteLayer(layer.id);
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          
          <div className="mb-4">
            <h3 className="font-bold mb-2">تنظیمات لایه</h3>
            {layers.map(layer => {
              if (layer.id !== selectedLayer) return null;
              return (
                <div key={`settings-${layer.id}`} className="bg-white p-2 rounded border border-gray-300">
                  <div className="mb-2">
                    <label className="block text-sm">نام:</label>
                    <input 
                      type="text" 
                      value={layer.name}
                      onChange={(e) => handleLayerPropertyChange(layer.id, 'name', e.target.value)}
                      className="w-full p-1 border border-gray-300 rounded"
                    />
                  </div>
                  <div className="mb-2">
                    <label className="block text-sm">رنگ:</label>
                    <input 
                      type="color" 
                      value={layer.color}
                      onChange={(e) => handleLayerPropertyChange(layer.id, 'color', e.target.value)}
                      className="w-full p-1 h-8 border border-gray-300 rounded"
                    />
                  </div>
                  <div className="mb-2">
                    <label className="block text-sm">قدرت لیزر (%):</label>
                    <input 
                      type="range" 
                      min="1" 
                      max="100" 
                      value={layer.power}
                      onChange={(e) => handleLayerPropertyChange(layer.id, 'power', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <span className="text-sm">{layer.power}%</span>
                  </div>
                  <div className="mb-2">
                    <label className="block text-sm">سرعت (mm/s):</label>
                    <input 
                      type="range" 
                      min="1" 
                      max="500" 
                      value={layer.speed}
                      onChange={(e) => handleLayerPropertyChange(layer.id, 'speed', parseInt(e.target.value))}
                      className="w-full"
                    />
                    <span className="text-sm">{layer.speed} mm/s</span>
                  </div>
                  <div className="mb-2">
                    <label className="block text-sm">حالت:</label>
                    <select 
                      value={layer.mode}
                      onChange={(e) => handleLayerPropertyChange(layer.id, 'mode', e.target.value)}
                      className="w-full p-1 border border-gray-300 rounded"
                    >
                      <option value="cut">برش</option>
                      <option value="engrave">حکاکی</option>
                    </select>
                  </div>
                </div>
              );
            })}
          </div>
          
          <div className="mb-4">
            <h3 className="font-bold mb-2">تنظیمات میز کار</h3>
            <div className="bg-white p-2 rounded border border-gray-300">
              <div className="mb-2">
                <label className="block text-sm">عرض (mm):</label>
                <input 
                  type="number" 
                  value={workspaceWidth}
                  onChange={(e) => setWorkspaceWidth(parseInt(e.target.value))}
                  className="w-full p-1 border border-gray-300 rounded"
                />
              </div>
              <div className="mb-2">
                <label className="block text-sm">طول (mm):</label>
                <input 
                  type="number" 
                  value={workspaceHeight}
                  onChange={(e) => setWorkspaceHeight(parseInt(e.target.value))}
                  className="w-full p-1 border border-gray-300 rounded"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Bottom Status Bar */}
      <div className="bg-gray-700 text-white p-2 flex justify-between">
        <div>ابعاد میز: {workspaceWidth} × {workspaceHeight} میلی‌متر</div>
        <div>تعداد اشکال: {shapes.length}</div>
        <div>ابزار فعلی: {currentTool === 'select' ? 'انتخاب' : currentTool === 'rect' ? 'مستطیل' : currentTool === 'line' ? 'خط' : 'دایره'}</div>
      </div>
    </div>
  );
}