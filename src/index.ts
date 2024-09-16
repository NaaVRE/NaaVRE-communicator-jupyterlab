import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the @naavre/communicator-jupyterlab extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: '@naavre/communicator-jupyterlab:plugin',
  description: 'Communication gateway for NaaVRE JupyterLab extensions',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log(
      'JupyterLab extension @naavre/communicator-jupyterlab is activated!'
    );
  }
};

export default plugin;
