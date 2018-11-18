const { app, BrowserWindow, globalShortcut  } = require('electron');
const fs = require('fs');
const fabric = require('fabric').fabric;
const {shell} = require('electron')
const {dialog} = require('electron')
const path = require('path');

const console = require('console');

//const ioHook = require('iohook');

const spawn = require("child_process").spawn;

/*
const pythonProcess = spawn('python',["../panelextractor.py", "", ""]);
pythonProcess.stdout.on('data', (data) => 
{
    // Do something with the data returned from python script
});
*/

app.console = new console.Console(process.stdout, process.stderr);


// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let win


app.on('ready', () => {
  globalShortcut.register('CommandOrControl+S', () => {
    console.log('CommandOrControl+S is pressed');
	win.webContents.send('SAVE_PANEL_DATA',"");
  })
})

/*
ioHook.on("keyup", event => {
   console.log(event); // {keychar: 'f', keycode: 19, rawcode: 15, type: 'keup'}
    
	win.webContents.send('KEYBORAD_KEY_STATE_CHANGED', event);
});
ioHook.start();

*/

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
  //win.webContents.send('Back_To_You',"Im ready");
  
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

/**
 Opens a file dialog to allow the user to select as 
 single comic page for post processing. 
 If processPanel is set to True this will instead run the 
 panel through the automated panel detector and then display
 the results on the editor for post processing. 
 */
exports.selectComicPage = function (processPanel = false) 
{
  var filePath  = dialog.showOpenDialog(win, {
    properties: ['openFile']
  });
  // TODO Handle empty file
  if(filePath.length ==0)
  {
	filePath = [''];
  }
  
    if(processPanel)
	{
		const pythonProcess = spawn('python',["../panelextractor.py", "-i", filePath[0]]);
		pythonProcess.stdout.on('data', (data) => 
		{
			// Do something with the data returned from python script
			win.webContents.send('Back_To_You',data);
			// TODO Sperate this logic into two method. One to allow just opening the panels
			// and one that will run the script on the panel and then load it. 
			comicMetadataInfo = loadComicPageDataHelper(filePath[0]);
			//win.webContents.send('Back_To_You', path.normalize(filePath[0]), jsonContent, comicMetadataInfo);
			win.webContents.send('EVENT_LOAD_PANEL', comicMetadataInfo);

		});
		pythonProcess.stderr.on('data', (data) => 
		{
			// Do something with the data returned from python script
			win.webContents.send('Back_To_You','Failed To Run');
			// TODO Handle Error cases. 
		});
	}	
	else
	{
		comicMetadataInfo = loadComicPageDataHelper(filePath[0]);
		//win.webContents.send('Back_To_You', path.normalize(filePath[0]), jsonContent, comicMetadataInfo);
		win.webContents.send('EVENT_LOAD_PANEL', comicMetadataInfo);
	}
  
};

/**
 Helper method to load a given comic page. 
 Given the path to a comic page, this method loads 
 all the metadata for the comic panels.
 @param filePath - Path to the comic page.
 @returns comicMetadataInfo
*/ 
function loadComicPageDataHelper(filePath)
{
  var pathNoExt = path.join(path.parse(filePath).dir, path.parse(filePath).name);
  console.error("Hello:");
  console.log(filePath);
  
  // TODO Handled file not existent
  // Load panel metadata file.
  var panelDataPath = pathNoExt + '.cpanel';
  var panelData = '';
  
  if(fs.existsSync(panelDataPath))
  {
	panelData = fs.readFileSync(panelDataPath);
	var jsonContent = JSON.parse(panelData);
  }
  else
  {
	jsonContent = {};
  }
  
  
  var comicMetadataInfo = {
	imagePath: path.normalize(filePath), // Path to the comic panel image.
	metadataPath: panelDataPath, // Path to the metadata file.
	metadata: jsonContent	// Loaded JSON comic panel metadata.
  };
  
  return comicMetadataInfo;

}

//ipcMain.on('REQUEST_COMIC_METADATA_STORE', saveComicPageMetadata);
/***
Given a comic info write it to a file.
**/
//function saveComicPageMetadata(event, comicMetadataToStore) 
exports.saveComicPageMetadata = function (comicMetadataToStore)
{
	var metadataPath = comicMetadataToStore.metadataPath;
	metadata = comicMetadataToStore.metadata;
	var json = JSON.stringify(metadata);
	fs.writeFileSync(metadataPath, json, 'utf8', new function(err)
		{
	
		});
};

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

/**
function sendKeyEvent(event)
{
	win.webContents.send('KEYBORAD_KEY_STATE_CHANGED', event);
}
**/

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