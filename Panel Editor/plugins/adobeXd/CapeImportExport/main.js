const application = require("application");
const fs = require("uxp").storage.localFileSystem;
const {Rectangle, Color, Text} = require("scenegraph");
const ImageFill = require("scenegraph").ImageFill;

const metadataExtension = '.cpanel';
var activeMetadata;

function rectangleHandlerFunction(selection)
{      // [2]

    const newElement = new Rectangle();             // [3]
    newElement.width = 100;
    newElement.height = 50;
    newElement.fill = new Color("Purple");

    selection.insertionParent.addChild(newElement); // [4]
    newElement.moveInParentCoordinates(100, 100);   // [5]

}

async function exportMetadataHandler()
{
  if(!activeMetadata)
  {
    return;
  }

  const folder = await fs.getFolder();
  var imageFilename = activeMetadata.imagePath;
  var outFilename = "test_"+imageFilename.split('.')[0]+metadataExtension;

  // TODO Extract panel data from the scene and update the metadata. 
  console.log(outFilename)
   try {
        // first create the entry and then write.
        var dataEntry = await folder.createEntry(outFilename, { overwrite: true});
        return await dataEntry.write(JSON.stringify(activeMetadata));
    }
    catch(e) {
        // report any errors here.
        console.log(e);
    }

  /*
  let renditionSettings = [{
    node: selection.items[0],               // refers to the first user-selected item in the document
    outputFile: file,                       // Set the outputFile property to the file constant we created
    type: application.RenditionType.PNG,    // Set the type property to application.RenditionType.PNG
    scale: 2                                // Set the desired scale of the exported rendition
    }];

    application.createRenditions(renditionSettings)    // The application#createRenditions method accepts as an argument the renditionSettings
    .then(results => {                                 // createRenditions returns a Promise.
        console.log(`PNG rendition has been saved at ${results[0].outputFile.nativePath}`);
    })
    .catch(error => {                              // Any errors will land in .catch
        console.log(error);
    });
    */

}

async function importMetadataHandler(selection)
{
    const comicImageFile = await fs.getFileForOpening({ types: ["jpg", "png"] });
    const fill = new ImageFill(comicImageFile);

    // Display image
    const shape = new Rectangle();
    shape.width = fill.naturalWidth;
    shape.height = fill.naturalHeight;

    shape.fill = fill;
    selection.insertionParent.addChild(shape);

    const aFile = await fs.getFileForOpening({ types: ["cpanel"] });   // [2]
    if (!aFile) return;                                             // [3]

    const contents = await aFile.read();                            // [4]

    const metadata = JSON.parse(contents);
    const text = new Text();                                        // [5]
    text.text = contents;
    text.styleRanges = [{
        length: contents.length,
        fill: new Color("#0000ff"),
        fontSize: 12
    }];

    //console.log(metadata.panels);
    var panels = metadata.panels;
    for(var i = 0; i < panels.length; i++)
    {
        var box = panels[i].box;
        console.log(box);
        const newElement = new Rectangle();
        newElement.width = box.w;
        newElement.height = box.h;
        newElement.fill = new Color("Purple", 0.5);

        selection.insertionParent.addChild(newElement);
        newElement.moveInParentCoordinates(box.x, box.y);
    }

    activeMetadata = metadata;
    //selection.insertionParent.addChild(text)                       // [6]
    //text.moveInParentCoordinates(10, 30);

}

module.exports =
{
    commands:
    {
        importMetadata: importMetadataHandler,
        exportMetadata: exportMetadataHandler
    }
};
