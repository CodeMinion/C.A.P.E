const { app, BrowserWindow, globalShortcut  } = require('electron');
const fs = require('fs');
const fabric = require('fabric').fabric;
const {shell} = require('electron')
const {dialog} = require('electron')
const path = require('path');
const console = require('console');
const spawn = require("child_process").spawn;
const { Menu, MenuItem } = require('electron')

const COMIC_IMAGE_EXTENSIONS = ["jpg","jepg", "jpe", "png", "bmp", "tiff", "tif"]
const COMIC_METADATA_EXTENSIONS = ["cpanel"];

var AdmZip = require('adm-zip');
app.console = new console.Console(process.stdout, process.stderr);

var mangaStyle = false;

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let win
let helpWin

/*
app.on('ready', () => {
globalShortcut.register('CommandOrControl+S', () => {
console.log('CommandOrControl+S is pressed');
win.webContents.send('SAVE_PANEL_DATA',"");
})
})
*/


const appMenu = new Menu();

const fileMenu = new Menu()
const viewMenu = new Menu();
const exportMenu = new Menu();
const helpMenu = new Menu();

appMenu.append(new MenuItem({
  label: 'File',
  submenu: fileMenu
}))

appMenu.append(new MenuItem({
  label: 'View',
  submenu: viewMenu
}))

appMenu.append(new MenuItem({
  label: 'Export',
  submenu: exportMenu
}))

appMenu.append(new MenuItem({
  label: 'Help',
  accelerator: 'F1',
  submenu: helpMenu,
}))


// File Menu
const saveMenuItem = new MenuItem({
  label: 'Save',
  accelerator: 'CmdOrCtrl+S',
  click: () => { win.webContents.send('SAVE_PANEL_DATA',""); }
});

const openMenuItem = new MenuItem({
  label: 'Open Page',
  accelerator: 'CmdOrCtrl+Shift+O',
  click: () => { win.webContents.send('OPEN_SINGLE_PANEL_DATA'); }
});

const processMenuItem = new MenuItem({
  label: 'Process Page',
  accelerator: 'CmdOrCtrl+Shift+P',
  click: () => { win.webContents.send('OPEN_SINGLE_PANEL_DATA', true); }
});

const openComicMenuItem = new MenuItem({
  label: 'Open Folder',
  accelerator: 'CmdOrCtrl+O',
  click: () => { win.webContents.send('OPEN_FOLDER_PANEL_DATA'); }
});

const processComicMenuItem = new MenuItem({
  label: 'Process Folder',
  accelerator: 'CmdOrCtrl+P',
  click: () => { win.webContents.send('OPEN_FOLDER_PANEL_DATA', true); }
});

fileMenu.append(saveMenuItem);
fileMenu.append(new MenuItem({type: 'separator'}));
fileMenu.append(openComicMenuItem);
fileMenu.append(processComicMenuItem);
fileMenu.append(new MenuItem({type: 'separator'}));
fileMenu.append(openMenuItem);
fileMenu.append(processMenuItem);
//////////////////////////////////////////////

// View Menu
const zoomActualMenu =new MenuItem({
  label: 'Actual Size',
  accelerator: 'CmdOrCtrl+0',
  click: () => { win.webContents.send('EVENT_ZOOM_ACTUAL',""); }
})
viewMenu.append(zoomActualMenu);


const zoomInMenu = new MenuItem({
  label: 'Zoom In',
  accelerator: 'CmdOrCtrl+=',
  click: () => { win.webContents.send('EVENT_ZOOM_IN',""); }
})
viewMenu.append(zoomInMenu);

const zoomOutMenu =new MenuItem({
  label: 'Zoom Out',
  accelerator: 'CmdOrCtrl+-',
  click: () => { win.webContents.send('EVENT_ZOOM_OUT',""); }
})
viewMenu.append(zoomOutMenu);

viewMenu.append(new MenuItem({type: 'separator'}));

const pageDownMenu =new MenuItem({
  label: 'Next Page',
  accelerator: 'CmdOrCtrl+PageDown',
  click: () => { win.webContents.send('EVENT_PAGE_NEXT',false); }
})
viewMenu.append(pageDownMenu);

const pageUpMenu =new MenuItem({
  label: 'Prev Page',
  accelerator: 'CmdOrCtrl+PageUp',
  click: () => { win.webContents.send('EVENT_PAGE_NEXT',true); }
})
viewMenu.append(pageUpMenu);
////////////////////////////////////////////////////////

// Export Menu
const exporCbzMenu =new MenuItem({
  label: 'Export as CBZ',
  accelerator: 'CmdOrCtrl+E',
  click: () => { win.webContents.send('EVENT_EXPORT_COMIC',"cbz"); }
})
exportMenu.append(exporCbzMenu);
/////////////////////////////////////////////////////////

// Help Menu
const controlsHelpMenuItem =new MenuItem({
  label: 'Controls Info',
  accelerator: 'F1',
  click: () => { helpWin.show(); }
})
helpMenu.append(controlsHelpMenuItem);
/////////////////////////////////////////////////////////

Menu.setApplicationMenu(appMenu)


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

exports.handleUserFileDrop = function(droppedFilePath)
{
  fs.lstat(droppedFilePath, (err, stats) =>
  {
    win.webContents.send('EVENT_LOG', 'File Found:'+stats);
    var processPanel = true;

    if (stats.isDirectory())
    {
      win.webContents.send('EVENT_LOG', 'Dir Found:'+droppedFilePath);
      comicImageFiles = getAllComicImageFilesFromDirectory(droppedFilePath);
      win.webContents.send('EVENT_LOG', comicImageFiles);
      loadComicFileFromFolder(droppedFilePath, comicImageFiles, processPanel);
    }
    else
    {
      if(isAllowedImagePath(droppedFilePath))
      {
        loadComicFileFromFile(droppedFilePath, processPanel);
      }
      win.webContents.send('EVENT_LOG', 'File Found:'+droppedFilePath);
    }
  });
}

/**
Allows the user to select an entire directory containing
comic panels. This will load each of the comic panels in the folder
and their metadata into the editor for updating.
If processPanel is set to true this will first run
the panel recognizer scrip to extract some initial panel data.
It will then output a list of comicMetadataInfo.
@param processPanel set to try if we want to pre-process the folder to extract panel data.
**/
exports.selectComicDirectory = function (processPanel = false) {

  var path  = dialog.showOpenDialog(win, {
    properties: ['openDirectory']
  });

  win.webContents.send('EVENT_LOG', path);

  if(!path || path.length ==0)
  {
    return;
  }

  var folderPath = path[0];
  var files = fs.readdirSync(folderPath);
  win.webContents.send('EVENT_LOG', files);

  comicImageFiles = getAllComicImageFilesFromDirectory(path[0]);

  win.webContents.send('EVENT_LOG', comicImageFiles);
  loadComicFileFromFolder(folderPath, comicImageFiles, processPanel);

}

/**
Returns a list of all the comic images inside a give folder.
**/
function getAllComicImageFilesFromDirectory(dirPath)
{
  var folderPath = dirPath;
  var files = fs.readdirSync(folderPath);
  win.webContents.send('EVENT_LOG', files);

  var comicImageFiles = []

  for (var i =0; i < files.length; i++)
  {
    var file = files[i];
    //win.webContents.send('EVENT_LOG', 'File Found:'+ file);
    var filename = getFilePath(folderPath, file);
    //win.webContents.send('EVENT_LOG', 'File Found:'+filename);

    var stat = fs.lstatSync(filename);
    if (stat.isDirectory())
    {
      //win.webContents.send('EVENT_LOG', "Dir :"+ filename);
      continue;
    }

    if(!isAllowedImagePath(filename))
    {
      // Not a valid image file.
      //win.webContents.send('EVENT_LOG', 'File Not Allowed:'+filename);
      continue;
    }

    //win.webContents.send('EVENT_LOG', 'Adding File:'+filename);
    comicImageFiles.push(filename);
  }
  return comicImageFiles;
}

/**
Given a folder and a list of comic files this method will load all the files
metadata. If processPanels is true, the entire directory wii be run through
the automate comic panel extraction process.
*/
function loadComicFileFromFolder(folderPath, listComicFile, processPanel = false)
{

  if (folderPath.length == 0)
  {
    return;
  }

  win.webContents.send('EVENT_LOAD_START');

  if(processPanel)
  {
    // TODO Signal Renderer to display progress.
    // Send folder to be scanned by the recognizer to extract the page panels.
    const pythonProcess = spawn('python',["recognizer/panelextractor.py", "-d", folderPath]);
    pythonProcess.stdout.on('data', (data) =>
    {
      var outMetaData = []
      for(var i = 0; i < listComicFile.length; i++)
      {
        comicMetadataInfo = loadComicPageDataHelper(listComicFile[i]);
        outMetaData.push(comicMetadataInfo);
      }

      win.webContents.send('EVENT_LOAD_PANEL', outMetaData[0]);
      win.webContents.send('EVENT_LOAD_PANELS_AREA', outMetaData);
      win.webContents.send('EVENT_LOAD_COMPLETE');

    });
    pythonProcess.stderr.on('data', (data) =>
    {
      // Do something with the error data returned from python script
      win.webContents.send('Back_To_You','Failed To Run');
      // TODO Handle Error cases.
    });
  }
  else
  {
    var outMetaData = []
    for(var i = 0; i < listComicFile.length; i++)
    {
      comicMetadataInfo = loadComicPageDataHelper(listComicFile[i]);
      outMetaData.push(comicMetadataInfo);
    }

    win.webContents.send('EVENT_LOAD_PANEL', outMetaData[0]);
    win.webContents.send('EVENT_LOAD_PANELS_AREA', outMetaData);
    win.webContents.send('EVENT_LOAD_COMPLETE');
  }

}

function getFilePath(folderPath, file)
{
  return path.join(folderPath,file);
}

function isAllowedImagePath(imagePath)
{
  var ext = path.parse(imagePath).ext;

  if(ext)
  {
    ext = ext.replace('.', '');
  }
  var valid =  COMIC_IMAGE_EXTENSIONS.includes(ext);

  win.webContents.send('EVENT_LOG', ext + " Valid : " +valid);

  return valid;

}

function isAllowedMetadataPath(imagePath)
{
  var ext = path.parse(imagePath).ext;

  if(ext)
  {
    ext = ext.replace('.', '');
  }
  var valid =  COMIC_METADATA_EXTENSIONS.includes(ext);
  return valid;

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
    properties: ['openFile'],
    filters: [
      //{ name: "All Files", extensions: ["*"] },
      { name: "Images", extensions: COMIC_IMAGE_EXTENSIONS },
    ],
  });

  // TODO Handle empty file
  if(!filePath || filePath.length ==0)
  {
    return;
  }

  loadComicFileFromFile(filePath[0], processPanel);

};

function loadComicFileFromFile(filePath, processPanel = false)
{
  win.webContents.send('EVENT_LOAD_START');
  if(processPanel)
  {
    // TODO Signal Renderer to display progress.
    const pythonProcess = spawn('python',["recognizer/panelextractor.py", "-i", filePath]);
    pythonProcess.stdout.on('data', (data) =>
    {
      // Do something with the data returned from python script
      //win.webContents.send('Back_To_You',data);
      comicMetadataInfo = loadComicPageDataHelper(filePath);
      //win.webContents.send('Back_To_You', path.normalize(filePath[0]), jsonContent, comicMetadataInfo);
      win.webContents.send('EVENT_LOAD_PANEL', comicMetadataInfo);
      win.webContents.send('EVENT_LOAD_COMPLETE');

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
    comicMetadataInfo = loadComicPageDataHelper(filePath);
    //win.webContents.send('Back_To_You', path.normalize(filePath[0]), jsonContent, comicMetadataInfo);
    win.webContents.send('EVENT_LOAD_PANEL', comicMetadataInfo);
    win.webContents.send('EVENT_LOAD_COMPLETE');
  }
}

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
  var id = 'w'+hashCode(path.parse(filePath).name);

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
    id: id,
    name: path.parse(filePath).name,
    folder: path.parse(filePath).dir,
    imagePath: path.normalize(filePath), // Path to the comic panel image.
    metadataPath: panelDataPath, // Path to the metadata file.
    metadata: jsonContent	// Loaded JSON comic panel metadata.
  };

  return comicMetadataInfo;

}

function hashCode(s) {
  for(var i = 0, h = 0; i < s.length; i++)
  h = Math.imul(31, h) + s.charCodeAt(i) | 0;
  return h;
}

/***
Given a comic info write it to a file.
**/
exports.saveComicPageMetadata = function (comicMetadataToStore)
{
  var metadataPath = comicMetadataToStore.metadataPath;
  metadata = comicMetadataToStore.metadata;
  // Sort Panels so they are in the proper reading order in the array.
  metadata.panels.sort(function(panelA, panelB)
  {
      if(panelA.box.y == panelB.box.y)
      {
         if(mangaStyle)
         {
           return panelB.box.x - panelA.box.x;
         }
         else
         {
           return panelA.box.x - panelB.box.x;
         }
      }
      return panelA.box.y - panelB.box.y;
  });

  var json = JSON.stringify(metadata);
  fs.writeFileSync(metadataPath, json, 'utf8', new function(err)
  {
    // Do nothing.
  });
};

exports.exportComic = function (pathToComicDir, packageFormat = 'cbz')
{
  var filePath  = dialog.showSaveDialog(win, {
    properties: ['saveFile'],
    filters: [
      //{ name: "All Files", extensions: ["*"] },
      //{ name: "Images", extensions: COMIC_IMAGE_EXTENSIONS },
    ],
  });

  win.webContents.send('EVENT_LOG', "Selection:" + filePath);

  if (!filePath || filePath.length == 0)
  {
    return;
  }

  var destPath = filePath;

  packageComicAsCBZ(pathToComicDir, destPath);

}


/**
Function to package all the comic images and metadata
files into a CBZ format to allow reading by comic apps.
**/
function packageComicAsCBZ(pathToComicDir, destPath)
{
  var zip = new AdmZip();

  var filesToPack = getAllComicPackagebleFiles(pathToComicDir);

  for(var i = 0; i < filesToPack.length; i++)
  {
    zip.addLocalFile(filesToPack[i]);
  }

  //win.webContents.send('EVENT_LOG', "Dest:" + destPath+'.cbz');
  zip.writeZip(destPath+'.cbz');
}

function getAllComicPackagebleFiles(path)
{
  var folderPath = path;
  var files = fs.readdirSync(folderPath);
  //win.webContents.send('EVENT_LOG', files);

  var comicImageFiles = []

  for (var i =0; i < files.length; i++)
  {
    var file = files[i];
    //win.webContents.send('EVENT_LOG', 'File Found:'+ file);
    var filename = getFilePath(folderPath, file);//path.join(folderPath,path.parse(file).filename);
    //win.webContents.send('EVENT_LOG', 'File Found:'+filename);

    var stat = fs.lstatSync(filename);
    if (stat.isDirectory())
    {
      //win.webContents.send('EVENT_LOG', "Dir :"+ filename);
      continue;
    }


    if(!isAllowedImagePath(filename) && !isAllowedMetadataPath(filename))
    {
      // Not a valid image file.
      continue;
    }


    //win.webContents.send('EVENT_LOG', 'Adding File:'+filename);
    comicImageFiles.push(filename);
  }

  return comicImageFiles;

}

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

  helpWin = new BrowserWindow({ width: 400, height: 400, show:false, parent: win });
  helpWin.setMenu(null);
  //win.webContents.on('Am_I_Ready', doSomething)

  console.log("Our");

  // and load the index.html of the app.
  win.loadFile('index.html');

  helpWin.loadFile('help.html');

  win.webContents.on('dom-ready', () => {
  });

  win.once('ready-to-show', () => {
    console.log("Here");
    win.show()

  });

  console.log("Our");


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
