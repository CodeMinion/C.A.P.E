const application = require("application");
const fs = require("uxp").storage.localFileSystem;
const {Rectangle, Color} = require("scenegraph");

function rectangleHandlerFunction(selection)
{      // [2]

    const newElement = new Rectangle();             // [3]
    newElement.width = 100;
    newElement.height = 50;
    newElement.fill = new Color("Purple");

    selection.insertionParent.addChild(newElement); // [4]
    newElement.moveInParentCoordinates(100, 100);   // [5]

}

async function exportMetadata()
{
  const folder = await fs.getFolder();
  const file = await folder.createFile("rendition.png");

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

}

async function importMetadata()
{

}

module.exports =
{
    commands:
    {
        importMetadata: rectangleHandlerFunction,
        exportMetadata: exportMetadata
    }
};
