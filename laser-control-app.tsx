import React, { useState, useRef, useEffect } from 'react';

export default function LaserControlApp() {
  // State for canvas drawing
  const canvasRef = useRef(null);
  const [drawing, setDrawing] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [shapes, setShapes] = useState([]);
  const [selectedShape, setSelectedShape] = useState(null);
  
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
    // This is a placeholder - in a real app, you would parse DXF files
    alert('DXF import functionality would be implemented here');
    
    // Simulate adding some shapes
    setShapes([
      ...shapes,
      {
        type: 'rect',
        x: 100,
        y: 100,
        width: 200,
        height: 150,
        layerId: selectedLayer
      },
      {
        type: 'circle',
        x: 300,
        y: 300,
        radius: 50,
        layerId: selectedLayer
      }
    ]);
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
            <button className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded" onClick={importDXF}>وارد کردن DXF</button>
            <button className="bg-green-600 hover:bg-green-700 px-3 py-1 rounded" onClick={startLaserJob}>شروع کار لیزر</button>
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