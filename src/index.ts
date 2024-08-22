import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the naavre-communicator extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'naavre-communicator:plugin',
  description: 'Communicate with NaaVRE services',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension naavre-communicator is activated!');
  }
};

export default plugin;
