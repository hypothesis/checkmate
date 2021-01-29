import './App.css';
import {
  Container,
  Dropdown,
  Input,
  Menu,
  Form,
} from 'semantic-ui-react'

import React from 'react';
import URLChooser from "./components/UrlViewer";


class App extends React.Component {
  render() {
    return (
        <div className="App">
          <Menu fixed='top' inverted>
            <Container>
              <Menu.Item as='a' header>
                Checkmate
              </Menu.Item>
              <Menu.Item as='a'>Home</Menu.Item>

              <Dropdown item simple text='Dropdown'>
                <Dropdown.Menu>
                  <Dropdown.Item>List Item</Dropdown.Item>
                  <Dropdown.Item>List Item</Dropdown.Item>
                  <Dropdown.Divider/>
                  <Dropdown.Header>Header Item</Dropdown.Header>
                  <Dropdown.Item>
                    <i className='dropdown icon'/>
                    <span className='text'>Submenu</span>
                    <Dropdown.Menu>
                      <Dropdown.Item>List Item</Dropdown.Item>
                      <Dropdown.Item>List Item</Dropdown.Item>
                    </Dropdown.Menu>
                  </Dropdown.Item>
                  <Dropdown.Item>List Item</Dropdown.Item>
                </Dropdown.Menu>
              </Dropdown>
            </Container>
          </Menu>

          <Container style={{marginTop: '7em'}}>
            <URLChooser />
          </Container>
        </div>
    );
  }
}

export default App;
