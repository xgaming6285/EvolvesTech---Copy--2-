( function( $ ){
	'use strict';

	// Parent class.
	var HandleCookie = function( cookieName ) {
		this.cookieName = cookieName;
	};

	HandleCookie.prototype.setCookie = function( name, value ) {
		var days = 30; // set cookie duration
		if ( days ) {
			var date = new Date();
			date.setTime( date.getTime() + ( days * 24 * 60 * 60 * 1000 ) );
			var expires = "; expires=" + date.toGMTString();
		}
		else var expires = "";
		document.cookie = name + "=" + value + expires + "; path=/;SameSite=Lax";
	};

	HandleCookie.prototype.getCookie = function( name ) {
		var value = "; " + document.cookie;
		var parts = value.split( "; " + name + "=" );
		if ( parts.length == 2 ) return parts.pop().split( ";" ).shift();
	};

	HandleCookie.prototype.create = function() {
		if ( ! this.getCookie( this.cookieName ) ) {
			this.setCookie( this.cookieName, '[]' );
		}
		this.list = JSON.parse( this.getCookie( this.cookieName ) );
	};

	HandleCookie.prototype.removeItem = function( carID ) {
		var filtered = this.list.filter( function( ele ) {
			return ele !== carID;
		} );
		this.setCookie( this.cookieName, JSON.stringify( filtered ) );
		this.list = filtered;
	};

	HandleCookie.prototype.isAdded = function( id ) {
		if ( this.list.length && this.list.includes( id ) ) {
			return true;
		}
		return false;
	};

	/* HandleCookie.prototype.setAddedListings = function( ctaBtn ) {
		let $item;
		if ( $( '.listing-item__inner' ).length ) {
			$item = $( '.listing-item__inner' );

		} else {
			$item = $( ctaBtn ).parent();

		}
		let showList = JSON.parse( this.getCookie( this.cookieName ) );
		for ( let i = 0; i < $item.length; i++ ) {
			if ( $.inArray( $( $item[i] ).attr( 'data-listing-id' ), showList ) !== -1 ) {
				var $tooltip = $( $item[i] ).find( '.image__cta__tooltip' );
				$( $item[i] ).find( ctaBtn ).addClass( 'visited' );
				$tooltip.text( $tooltip.attr( 'data-remove-text' ) );
			}
		}
	}; */

	var CompareList = function( cookieName ) {
		HandleCookie.call( this, cookieName ); // equal to this.cookieName = cookieName
	};
	// extend class
	CompareList.prototype = Object.create( HandleCookie.prototype );

	CompareList.prototype.init = function() {
		this.list               = [];
		this.$compareNumber     = $( '.compare__badge' );
		this.$compareRemoveItem = $( '.compare-item-remove' );

		this.create( this.cookieName );
		this.handleAddRemove();
		this.handleClickToRemove();
		this.setCompareBadge();
	};
	CompareList.prototype.addItem = function( carID ) {
		this.list = this.list.concat( carID );
		this.setCookie( this.cookieName, JSON.stringify( this.list ) );
	};

	CompareList.prototype.handleAddRemove = function() {
		var self = this;
		$( 'body' ).on( 'click', '.image__cta__compare', function() {
			var $this = $( this );
			var carID = $this.closest( '.image__cta' ).attr( 'data-listing' );
			var $tooltip = $this.find( '.image__cta__tooltip' );
			if ( self.isAdded( carID ) ) {
				$this.removeClass( 'visited' );
				$tooltip.text( $tooltip.attr( 'data-add-text' ) );
				self.removeItem( carID );
			} else if ( self.list.length < 3 ) {
				$this.addClass( 'visited' );
				$tooltip.text( $tooltip.attr( 'data-remove-text' ) );
				self.addItem( carID );
			} else {
				alert( ALCompare.addListingAlert );
			}
			self.setCompareBadge();
		} );

		$( 'body' ).on( 'click', '.single-listing__compare', function( e ) {
			e.preventDefault();
			var $this = $( this );
			var carID = $this.parent().attr( 'data-listing-id' );
			if ( self.isAdded( carID ) ) {
				$this.removeClass( 'visited' );
				self.removeItem( carID );
			} else if ( self.list.length < 3 ) {
				$this.addClass( 'visited' );
				self.addItem( carID );
			} else {
				alert( ALCompare.addListingAlert );
			}
			self.setCompareBadge();
		} );
	};

	CompareList.prototype.handleClickToRemove = function() {
		var self = this;
		this.$compareRemoveItem.on( 'click', function() {
			var $this = $( this );
			var $wrapper = $this.closest( '.compare-item' );

			self.removeItem( $this.attr( 'data-listing-id' ) );

			$( $wrapper ).find( '.compare-item__image' ).attr( 'src', $wrapper.attr( 'data-default-img' ) );
			$( $wrapper ).find( '.compare-item__title' ).text( '' );
			$( $wrapper ).find( '.compare-item__link' ).attr( 'href', $wrapper.attr( 'data-default-link' ) );
			$( $wrapper ).find( 'td[data-listing-option="rating"]' ).html( '' );
			$( $wrapper ).find( 'td[data-listing-option="price"]' ).html( '' );
			$( $wrapper ).find( 'td[data-listing-option="dealer"]' ).html( '' );
			$( $wrapper ).find( 'td[data-listing-option="body"]' ).html( '' );
			$( $wrapper ).find( 'td[data-listing-option="mileage"]' ).html( '' );
			$( $wrapper ).find( 'td[data-listing-option="fuel-type"]' ).text( '' );
			$( $wrapper ).find( 'td[data-listing-option="engine"]' ).text( '' );
			$( $wrapper ).find( 'td[data-listing-option="year"]' ).text( '' );
			$( $wrapper ).find( 'td[data-listing-option="transmission"]' ).text( '' );
			$( $wrapper ).find( 'td[data-listing-option="drive"]' ).text( '' );
			$( $wrapper ).find( 'td[data-listing-option="exterior-color"]' ).html( '' );
			$( $wrapper ).find( 'td[data-listing-option="interior-color"]' ).html( '' );
			$( $wrapper ).find( 'td[data-listing-option="extra-feature"]' ).html('' );
			$( $wrapper ).addClass( 'is-empty' );

			if ( ! self.list.length ) {
				$( '.compare-no-listing-link' ).removeClass( 'is-hidden' );
				$( '.compare-wrapper' ).addClass( 'is-hidden' );
			}

			self.setCompareBadge();
		} );
	};

	CompareList.prototype.setCompareBadge = function() {
		var carNumber = this.list.length;
		if ( carNumber ) {
			this.$compareNumber.removeClass( 'is-hidden' ).text( carNumber );
		} else {
			this.$compareNumber.addClass( 'is-hidden' );
		}
	};

	var FavouriteList = function( cookieName ) {
		HandleCookie.call( this, cookieName ); // equal to this.cookieName = cookieName
	};
	// extend class
	FavouriteList.prototype = Object.create( HandleCookie.prototype );

	FavouriteList.prototype.init = function() {
		this.list = [];

		this.create( this.cookieName );
		this.handleAddRemove();
	};

	FavouriteList.prototype.handleAddRemove = function() {
		var self = this;
		$( 'body' ).on( 'click', '.image__cta__favorite', function() {
			var $this = $( this );
			var carID = $this.closest( '.image__cta' ).attr( 'data-listing' );
			var $tooltip = $this.find( 'b' );
			if ( self.isAdded( carID ) ) {
				$this.removeClass( 'visited' );
				$tooltip.text( $tooltip.attr( 'data-add-text' ) );
				self.removeItem( carID );
			} else {
				$this.addClass( 'visited' );
				$tooltip.text( $tooltip.attr( 'data-remove-text' ) );
				self.addItem( carID );
			}
		} );
		$( 'body' ).on( 'click', '.single-listing__save', function( e ) {
			e.preventDefault();
			var $this = $( this );
			var carID = $this.parent().attr( 'data-listing-id' );
			if ( self.isAdded( carID ) ) {
				$this.removeClass( 'visited' );
				self.removeItem( carID );
			} else {
				$this.addClass( 'visited' );
				self.addItem( carID );
			}
		} );
	};

	FavouriteList.prototype.addItem = function( carID ) {
		var list = this.list;
		this.list = list.concat( carID );
		this.setCookie( this.cookieName, JSON.stringify( this.list ) );
	};

	var compare = new CompareList( 'compareList' );
	var favourite = new FavouriteList( 'favouriteList' );
	compare.init();
	favourite.init();

} )( jQuery );
