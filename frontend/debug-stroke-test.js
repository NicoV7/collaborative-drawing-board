// Simple test to check stroke update logic flow
console.log('Testing stroke update flow...');

// Simulate the test scenario
let isDrawing = false;
let currentStroke = [];
let strokeBuffer = [];
let onStrokeUpdate = jest.fn();
let mockRafCallbacks = [];
let optimizeFor60FPS = true;

global.requestAnimationFrame = jest.fn((callback) => {
  mockRafCallbacks.push(callback);
  return mockRafCallbacks.length;
});

// Simulate mouse down (should set isDrawing to true)
console.log('1. Mouse down - setting isDrawing to true');
isDrawing = true;

// Simulate mouse move events
console.log('2. Mouse move events...');
for (let i = 0; i < 3; i++) {
  console.log(`   Mouse move ${i}: x=${100 + i * 10}, y=${150 + i * 5}`);
  
  if (!isDrawing) {
    console.log('   Skipped - not drawing');
    continue;
  }
  
  const pos = { x: 100 + i * 10, y: 150 + i * 5 };
  
  // Add point to buffer
  strokeBuffer.push(pos.x, pos.y);
  console.log(`   Added point, buffer now: [${strokeBuffer.join(', ')}]`);
  
  // Trigger RAF
  if (optimizeFor60FPS) {
    console.log(`   Requesting animation frame... (${mockRafCallbacks.length + 1})`);
    global.requestAnimationFrame(() => {
      console.log('   RAF callback executing');
      currentStroke = [...strokeBuffer];
      onStrokeUpdate({
        x: pos.x,
        y: pos.y, 
        points: [...strokeBuffer],
        timestamp: Date.now(),
        pressure: 1,
      });
    });
  }
}

console.log('\n3. Processing RAF callbacks...');
mockRafCallbacks.forEach((callback, i) => {
  console.log(`   Executing RAF callback ${i}`);
  callback();
});

console.log('\n4. Final results:');
console.log('   onStrokeUpdate call count:', onStrokeUpdate.mock.calls.length);
console.log('   RAF callbacks:', mockRafCallbacks.length);

function jest_fn() {
  const calls = [];
  const fn = function(...args) {
    calls.push(args);
  };
  fn.mock = { calls };
  return fn;
}

global.jest = { fn: jest_fn };