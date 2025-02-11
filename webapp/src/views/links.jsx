import * as React from 'react';

import * as tabs from '../controllers/tabs';
import { SingleProvider, SearchProvider } from '../models/providers';

class CompositeLink extends React.Component
{
    render() {
        if( this.props.actions && this.props.actions.length > 0 ) {
            return (
                <span>
                    <a href='#' onClick={ this.props.onClick }>{ this.props.label }</a>
                    { '(' }
                        {  this.props.actions.map( ( it, i ) => (
                                <span key={ i }>
                                    { i > 0 && ', ' }
                                    <a href='#' onClick={ it.onClick }>{ it.label }</a>
                                </span>
                        ) ) }
                    { ')' }
                </span>
            );
        } else {
            return (
                <a href='#' onClick={ this.props.onClick }>{ this.props.label }</a>
            );
        }
    }
}

export class ObjectLink extends React.Component
{
    render() {
        return (
            <CompositeLink label={ this.props.label }
                           onClick={ () => {
                                var provider = new SingleProvider( this.props.target );
                                tabs.create_display_tab( this.props.label, provider );
                            } }
                           actions={ this.props.actions }/>
        );
    }
}

export class TagLink extends React.Component
{
    render() {
        return (
            <a className='taglink'
               href='#'
               onClick={ () => {
                    var provider = new SearchProvider( { query: this.props.tag } );
                    tabs.create_display_tab( this.props.tag, provider );
                } }>{ this.props.label }</a>
        );
    }
}
