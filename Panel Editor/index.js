const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const fabric = require('fabric').fabric;
const {shell} = require('electron')
const {dialog} = require('electron')
const path = require('path');

const console = require('console');


app.console = new console.Console(process.stdout, process.stderr);
//console.log("Logging...");
//console.warn("Hello");
//console.error("Hello");

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let win

/*
document.addEventListener('DOMContentLoaded', function () {

	var canvas = new fabric.StaticCanvas(null, { width: 300, height: 250 });	
	
});

*/

// Register to receive IPC events from the Render process. 
const {ipcMain} = require('electron');
ipcMain.on('Am_I_Ready', doSomething)

function doSomething(){
	//var canvas = new fabric.StaticCanvas(null, { width: 300, height: 250 });	
	
  console.log('Everything is ready.');
  // Send IPC event to the Current Render process for this window. 
  win.webContents.send('Back_To_You',"Im ready");
  
  // Open a folder window but can't select. 
  //shell.openItem('C:\\')
  //shell.showItemInFolder('C:\\');
}

function selectDirectory()
{
	dialog.showOpenDialog(win, {
    properties: ['openDirectory']
  })
 
}

exports.selectDirectory = function () {
	
	var path  = dialog.showOpenDialog(win, {
    properties: ['openDirectory']
  });
  console.error("Hello:");
  console.log(path);
  
}

exports.selecComicPage = function () 
{
  var filePath  = dialog.showOpenDialog(win, {
    properties: ['openFile']
  });
  // TODO Handle empty file
  if(filePath.length ==0)
  {
	filePath = [''];
  }
  
  var pathNoExt = path.join(path.parse(filePath[0]).dir, path.parse(filePath[0]).name);
  console.error("Hello:");
  console.log(filePath);
  
  // TODO Handled file not existent
  // Load panel metadata file.
  var panelData = '';
  var panelDataPath = pathNoExt + '.cpanel';
  panelData = fs.readFileSync(panelDataPath);
  var jsonContent = JSON.parse(panelData);
  
  
  win.webContents.send('Back_To_You', path.normalize(filePath[0]), jsonContent);
  
}

// Install notes on windeos
/*
- npm config set msvs_version 2015
- Used node 8
- Install Microsoft Build Tools 2015 https://www.microsoft.com/en-us/download/confirmation.aspx?id=48159
- Set environment variable: SET VCTargetsPath=C:\Program Files (x86)\MSBuild\Microsoft.Cpp\v4.0\v140
- Run: npm install --msvs_version=2015
- npm install jsdom
- Run npm install fabric
- Requires Electron Version 2.0.8 beause it has Node 8.9.3 which is supported by fabric.
- set NODE_ENV="development"
*/
function createWindow () {
  // Create the browser window.
  win = new BrowserWindow({ width: 800, height: 600, show:false });

  //win.webContents.on('Am_I_Ready', doSomething)

  console.log("Our");
  
  // and load the index.html of the app.
  win.loadFile('index.html');
  
  win.webContents.on('dom-ready', () => {
  //win.webContents.once('did-finish-load', () => {
  // Call here to ensure the DOM is ready. NOPE
	//var canvas = new fabric.StaticCanvas(null, { width: 300, height: 250 });	
	//var canvas = new fabric.Canvas();
	//canvas.backgroundColor="red";
	//canvas.setHeight(1500);
	//canvas.setWidth(1500);

  });
  win.once('ready-to-show', () => {
	console.log("Here");
    win.show()
	
  });
  
  console.log("Our");
    
  //"canvas": "^1.6.13",
   //"jsdom": "^9.12.0",
    
  // "canvas": "^2.1.0",
  //"electron": "^3.0.9",
  //var canvas = new fabric.Canvas();
  //var canvas = new fabric.StaticCanvas(null, { width: 300, height: 250 });	
 //canvas.setHeight(1500);
	//canvas.setWidth(1500);

   // Open the DevTools.
   win.webContents.openDevTools()
  
  // Emitted when the window is closed.
  win.on('closed', () => {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    win = null
  })
}

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow)

// Quit when all windows are closed.
app.on('window-all-closed', () => {
  // On macOS it is common for applications and their menu bar
  // to stay active until the user quits explicitly with Cmd + Q
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('activate', () => {
  // On macOS it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (win === null) {
    createWindow()
  }
})

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.