import React from 'react';
import {Segment, Form, Input, Icon, Table, Header} from "semantic-ui-react";

import './UrlViewer.css';

class CheckmateAPI {
    static HTTP_OPTIONS = {
        method: "GET",
        headers: {
            "Accept": "application/json"
        }
    }

    static analyzeURL(url, onSuccess) {
        let apiUrl = "/ui/api/analyze?url=" + encodeURIComponent(url)

        fetch(apiUrl, CheckmateAPI.HTTP_OPTIONS)
            .then(response => response.json())
            .then(payload => {
                onSuccess(payload);
            })
    }
}

class URLChooser extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            inputUrl: ""
        };
    }


    render() {
        const urlForm = <Form>
          <Form.Field>
            <label>URL to analyze</label>
            <Input
                ref={this.inputRef}
                placeholder='http://example.com/...'
                onChange={this.handleChange}
                action={{
                    content: "Analyze",
                    onClick: () => this.handleClick()
                }}
            />
          </Form.Field>
        </Form>;

        if (!this.state.analysis) {
            return urlForm;
        }

        const detections = this.state.analysis.relationships.detections.data;

        if (!detections || !detections.length) {
            return <React.Fragment>
                {urlForm}
                <Segment color="green">
                    <Icon name="info" />
                    This website is already allowed.
                </Segment>
            </React.Fragment>
        }

        return <React.Fragment>
            {urlForm}

            <URLMeta {...this.state.analysis.meta}/>

            <CheckmateDetections detections={detections} />

            <Segment>
                <EditableURL url={this.state.analysis.links.raw} {...this.state.analysis.attributes} />
            </Segment>
            </React.Fragment>
    }

    handleChange = (event) => {
        this.setState({"inputUrl": event.target.value})
    }

    handleClick = () => {
        CheckmateAPI.analyzeURL(this.state.inputUrl, (payload) =>  this.setState({"analysis": payload}))
    }

}

class CheckmateDetection extends React.Component {
    render() {
        return <Table.Row>
            <Table.Cell>{this.props.attributes.source}</Table.Cell>
            <Table.Cell>{this.props.attributes.reason}</Table.Cell>
        </Table.Row>
    }
}

class CheckmateDetections extends React.Component {
    render() {
        if (!this.props.detections.length) {
            return <React.Fragment/>;
        }

        return <Table celled stripe>
            <Table.Header>
             <Table.Row>
                <Table.HeaderCell colSpan='2'>Block list detections</Table.HeaderCell>
             </Table.Row>
            </Table.Header>
            <Table.Body>
                {this.props.detections.map(detection => <CheckmateDetection {...detection}/>)}
            </Table.Body>
        </Table>
    }
}

class URLMeta extends React.Component {
    render() {
        const headline = this.getHeadline()

        if (!headline) {
            return <React.Fragment/>;
        }

        return <Segment raised color={headline.color}>
            <Icon name={headline.icon} />
            {headline.message}
        </Segment>
    }

    getHeadline() {
        if (!this.props.isValid) {
            return {"message": "This URL is not valid", "color": "red", "icon": "ban"}
        }
        else if (!this.props.isPublic) {
            return {"message": "This URL is not publically accessible", "color": "red", "icon": "ban"}
        }
        else if (this.props.isIPv4) {
            return {"message": "This URL appears to be an IP address", "color": "orange", "icon": "warning"}
        }
    }
}

class EditableURL extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            rawURL: ''
        };
    }

    static getDerivedStateFromProps(nextProps, prevState) {
        if (nextProps.url === prevState.url) {
            return {};
        }

        return {
            url: nextProps.url,
            subDomainEnabled: nextProps.subDomains.map(() => true),
            pathEnabled: false,
            queryEnabled: false,
        }
    }

    setURLState(part, enabled, index=0) {
        const newState = {}

        if (part === "path") {
            newState["pathEnabled"] = enabled

            if (!enabled) {
                newState["queryEnabled"] = false
            }
        }
        else if (part === "query") {
            newState["queryEnabled"] = enabled

            if (enabled) {
                newState["pathEnabled"] = true
            }
        }

        if (enabled && (part === "path" || part === "query")){
            // Always re-enable the full domain if the query or path is set
            part = "subDomain"
        }

        if (part === "subDomain") {
            newState["subDomainEnabled"] = this.state.subDomainEnabled.slice();

            if (enabled) {
                for (let i = index; i < newState["subDomainEnabled"].length; i++) {
                     newState["subDomainEnabled"][i] = true;
                }
            }
            else {
                // If we're removing sub-domains, we should be removing the query
                // and path too
                newState["queryEnabled"] = false
                newState["pathEnabled"] = false

                for (let i = 0; i <= index; i++) {
                     newState["subDomainEnabled"][i] = false;
                }
            }
        }

        this.setState(newState)
    }

    getFinalUrl() {
        let url = this.props.scheme + '://';

        this.props.subDomains.forEach((subDomain, i) => {
            if (this.state.subDomainEnabled[i]) {
                url += subDomain + '.'
            }
        })

        url += this.props.rootDomain;
        url += this.state.pathEnabled ? this.props.path : '/';

        if (this.state.queryEnabled) {
             url += '?' + this.props.query;
        }

        return url;
    }

    render() {
        if (!this.state) {
            return <div />
        }

        const query = this.props.query;
        const path = this.props.path || '/';

        return <React.Fragment>
            {this.props.subDomains.map(
                (subDomain, i) => <URLComponent
                    value={subDomain + '.'}
                    enabled={this.state.subDomainEnabled[i]}
                    callback={(state) => this.setURLState("subDomain", state, i)}
                    label="sub"
                />
            )}

            <URLComponent
                value={this.props.rootDomain}
                fixed
                label="domain"
            />

            {path ? <URLComponent
                value={path}
                label="path"
                enabled={this.state.pathEnabled}
                callback={(state) => this.setURLState("path", state)}
                fixed={path === '/'}
            />: ''}

            {query ? <URLComponent
                label="query"
                value={'?' + query}
                enabled={this.state.queryEnabled}
                callback={(state) => this.setURLState("query", state)}
            />: ''}

            <Segment><code>{this.getFinalUrl()}</code></Segment>

        </React.Fragment>;
    }
}


class URLComponent extends React.Component {
    static defaultProps = {
        enabled: true,
        fixed: false,
    }
    render() {
        let className = "URLComponent " + (
            this.props.fixed ? "fixed":
            this.props.enabled ? "enabled": "disabled")

        return <button
            className={className}
            onClick={this.props.fixed ? null : this.handleClick}
            >
                <span>{this.props.value}</span>
                <label>{this.props.label}</label>
        </button>

    }

    handleClick = () => {
        if (this.props.callback !== undefined) {
            this.props.callback(!this.props.enabled);
        }
    }
}

export default URLChooser;