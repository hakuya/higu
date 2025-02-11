import * as React from 'react';
import * as ReactBootstrap from 'react-bootstrap';

import $ from 'jquery';
import 'jquery-ui/ui/widgets/droppable';

import * as dialogs from '../controllers/dialogs';

export class TagDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
            query: '',
            history: [],
            errText: '',
            badKey: null
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            query: this.state.query,
            history: this.state.history,
            errText: '',
            badKey: null
        } );
        this.obj = data.obj;
    }
    onApply( evt ) {
        evt.preventDefault();

        var tags = $( '#tags' ).val();
        this.obj.tag( tags, this.onApplyCallback.bind( this ) );

    }
    onApplyCallback( r )
    {
        var tags = $( '#tags' ).val();

        if( r.result == 'ok' ) {
            $( document ).focus();
            this.setState( {
                show: false,
                query: tags,
                history: this.state.history.filter( ( it ) => {
                                return it != tags;
                            } ).concat( [ tags ] ),
                errText: '',
                badKey: null
            } );
        } else {
            var badKey = null;
            if( r.msg ) {
                const match_res = r.msg.match( new RegExp( "\"(.*)\"" ) );
                if( match_res ) {
                    badKey = match_res[1];
                }
            }
            this.setState( {
                show: true,
                query: tags,
                history: this.state.history,
                errText: r.msg,
                badKey: badKey
            } );
        }
    }
    onCancel() {
        this.setState( {
            show: false,
            query: this.state.query,
            history: this.state.history,
            errText: '',
            badKey: null
        } );
    }
    onInputKey( evt ) {
        if( evt.keyCode != 38 && evt.keyCode != 40 ) return;
        evt.preventDefault();

        var query = $( '#tags' ).val();
        var idx = this.state.history.findIndex( ( it ) => {
                        return it == query;
                    } );
        if( evt.keyCode == 38 ) {
            if( idx < 0 ) {
                idx = this.state.history.length;
            }
            idx -= 1;
            if( idx < 0 ) {
                return;
            }
        } else if( evt.keyCode == 40 ) {
            idx += 1;
            if( idx <= 0 || idx >= this.state.history.length ) {
                return;
            }
        }

        $( '#tags' ).val( this.state.history[idx] );
    }
    onEntered() {
        $( '#tags' ).focus();
        $( '#tags' ).select();
    }
    componentDidMount() {
        dialogs.register_dialog( 'tag', this );
    }
    componentDidUpdate( prevProps, prevState ) {
        if( this.state.show
         && this.state.badKey
         && this.state.badKey != prevState.badKey )
        {
            var tags = $( '#tags' ).val();
            var index = tags.indexOf( this.state.badKey );
            if( index >= 0 ) {
                $( '#tags' )[0].setSelectionRange( index, index + this.state.badKey.length );
            }
        }
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onEntered={ this.onEntered.bind( this ) }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Tag Image</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Enter a series of tags separated by spaces.
                    Prefix a tag with a dash to remove it<br/>
                    <span id='tag-err-text' className='err-text'>{ this.state.errText }</span></p>
                    <form id='tag-dialog-form' onSubmit={ this.onApply.bind( this ) }><fieldset>
                    <label htmlFor='tags' style={{ paddingRight: '6px' }}>Tags</label>
                    <input type='text'
                           name='tags'
                           id='tags'
                           style={{
                                width: '90%',
                            }}
                           defaultValue={ this.state.query }
                           onKeyDown={ this.onInputKey.bind( this ) }/>
                    </fieldset></form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onApply.bind( this ) }>Apply</Button>
                    <Button variant="secondary" onClick={ this.onCancel.bind( this ) }>Cancel</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

export class DupDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            received: data.received,
            dropped: data.dropped,
        } );
        this.obj = data.obj;
    }
    onLink() {
        this.obj.set_variant( this.state.received, this.state.dropped );
        this.setState( {
            show: false,
        } );
    }
    onMerge() {
        this.obj.link_duplicates( this.state.received, this.state.dropped );
        this.setState( {
            show: false,
        } );
    }
    onCancel() {
        this.setState( {
            show: false,
        } );
    }
    componentDidMount() {
        dialogs.register_dialog( 'dup', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Link Image</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Select the relationship of the dropped image:</p>
                    <ul>
                        <li>Link: the dropped file is a variation</li>
                        <li>Merge: the dropped file is a duplicate</li>
                    </ul>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onLink.bind( this ) }>Link</Button>
                    <Button variant="secondary" onClick={ this.onMerge.bind( this ) }>Merge</Button>
                    <Button variant="secondary" onClick={ this.onCancel.bind( this ) }>Cancel</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

export class NameDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
        }
    }
    show( data ) {
        this.setState( {
            show: true,
        } );
        this.obj = data.obj;
    }
    onApply( evt ) {
        evt.preventDefault();

        var name = $( '#fname' ).val();
        var saveOld = $( '#saveold' ).is( ':checked' );

        if( name == '' ) {
            alert( 'Please enter a name' );
            return;
        } else if( name == '-' ) {
            name = null;
        }

        this.obj.rename( name, saveOld );

        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    onCancel() {
        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    onEntered() {
        $( '#fname' ).focus();
    }
    componentDidMount() {
        dialogs.register_dialog( 'name', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onEntered={ this.onEntered.bind( this ) }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Rename Image</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <p>Enter a new filename, or use '-' to clear the name.</p>

                    <form id='name-dialog-form' onSubmit={ this.onApply.bind( this ) }><fieldset>
                    <label htmlFor='fname'>Name</label>
                    <input type='text' name='fname' id='fname'/>
                    { ' ' }
                    <label htmlFor='saveold'>Save old name</label>
                    <input type='checkbox' name='saveold' id='saveold'/>
                    </fieldset></form>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onApply.bind( this ) }>Apply</Button>
                    <Button variant="secondary" onClick={ this.onCancel.bind( this ) }>Cancel</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

export class TextDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
            text: ''
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            text: data.text
        } );
    }
    onCancel() {
        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    componentDidMount() {
        dialogs.register_dialog( 'text', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Info</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <textarea id='info-text'
                              style={{
                                    width: '100%',
                                    height: '100%',
                                    resize: 'none'
                                }}
                              rows={ 10 }
                              defaultValue={ this.state.text }
                              readOnly={ true }/>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onCancel.bind( this ) }>OK</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}

export class ErrorDialog extends React.Component
{
    constructor( props ) {
        super( props );
        this.state = {
            show: false,
            msg: ''
        }
    }
    show( data ) {
        this.setState( {
            show: true,
            msg: data.msg
        } );
    }
    onCancel() {
        $( document ).focus();
        this.setState( {
            show: false,
        } );
    }
    componentDidMount() {
        dialogs.register_dialog( 'err', this );
    }
    render() {
        var Button = ReactBootstrap.Button;
        var Modal = ReactBootstrap.Modal;

        return (
            <Modal show={ this.state.show }
                   onHide={ this.onCancel.bind( this ) }>
                <Modal.Header closeButton>
                    <Modal.Title>Oops, something went wrong</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <span id='error-msg' dangerouslySetInnerHTML={{ __html: this.state.msg }}></span>
                </Modal.Body>
                <Modal.Footer>
                    <Button variant="primary" onClick={ this.onCancel.bind( this ) }>OK</Button>
                </Modal.Footer>
            </Modal>
        );
    }
}
