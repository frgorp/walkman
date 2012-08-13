// pandora player only allows 3 choosable songs. It scrolls throught the list
// giving the user to replay the previous song or skip ahead to the next

(function($, undefined) {
	jPandoraPlayer = function(cssSelector, playlist, options, currentStation) {
		jPlayerPlaylist.call(this, cssSelector, playlist, options);
		this.options = $.extend(true, this._pandoraOptions, this.options);
		this.currentStation = currentStation;
		this._getMoreSongs(true);
		this.buffer = [];
		this.buffering = false;
	}

	jPandoraPlayer.prototype = Object.create(new jPlayerPlaylist(), {
		_pandoraOptions : { value: 
			{
				pandora: {
					expireSec: 60 * 30,
					waitMillis: 250,
					maxSongs: 3,
					minSongs: 3,
					focusIndex: 1
				}
			},enumerable: true, configurable: true, writable: true 
		},
		buffer : { value: null, enumerable: true, configurable: true, writable: true },	
		buffering : { value: null, enumerable: true, configurable: true, writable: true },	
		_delay : { value: 
			function(millis) {
				var startTime = new Date();
				var currentTime = undefined;
				do {
					currentTime = new Date();
				} while (currentTime - startTime < millis);
			}, enumerable: true, configurable: true, writable: true 	
		},
		_getExpireTime : { value: function(offset) {
				var currentTime = new Date();
				currentTime.setSeconds(currentTime.getSeconds() + offset? offset : this.options.pandora.expireSec);
				return currentTime;
			}, enumerable: true, configurable: true, writable: true
		},
		_hasExpired : { value: function(song) {
				var currentTime = new Date();
				return song['expire'] < currentTime? true : false;
			},enumerable: true, configurable: true, writeable: true
		},
		_bufferSongs : { value: function(callback) {
				if (this.buffering) {
					return;
				}
				this.buffering = true;
				var player = this;
				$.post('api/songs', {stationId: this.currentStation}, function(data) {
					if (data['success'] = true) {
						for (song in data['songs']) {
							var newSong = data['songs'][song];
							newSong['expire'] = player._getExpireTime();
							player.buffer.push(newSong);
						}
						if ($.isFunction(callback)) {
							callback.call(this);
						}
					}
					player.buffering = false;
				}, "json")
				.error(function() {
					player.buffering = false;
				});
			}, enumerable: true, configurable: true, writable: true 
		},
		_getMoreSongs : { value: function(startPlaylist, playNext) {
				var player = this;
				this._bufferSongs(function() {
					while (player.playlist.length < player.options.pandora.minSongs &&
					player.buffer.length > 0) {
						player.add(player.buffer.shift());
						player._delay(player.options.pandora.delayMillis);
					}
					if (startPlaylist) {
						player.select(0);
						player._delay(player.options.pandora.waitMillis);
						player.play();
					}
					else if (playNext) {
						player.next();
					}
				});
			}, enumerable: true, configurable: true, writable: true 
		},
		currentStation : { value: null, enumerable: true, configurable: true, writable: true },	
		play : { value: function(index) {
			//	if (!this.playlist.length) {
			//		this._getMoreSongs(false, true);
			//	}
				//if (!this._hasExpired(this.playlist[index? index : 0])) {
					jPlayerPlaylist.prototype.play.apply(this, [index]);
					if (this.currentSong().songRating) {
						$("#pandora-upvote-icon").attr("src", "images/arrow-liked.png");
					}
					else {
						$("#pandora-upvote-icon").attr("src", "images/grey-up.png");
					}
				//}
		//		else {
		//			this.hardRemove(index);
		//			this.next();
		//		}
			/*	if (this.playlist.length > this.options.pandora.maxSongs) {
					for (i = 0; i < this.playlist.length - this.options.pandora.maxSongs; i++) {
						if (this.current == 0) {
							break;
						}
						//this._delay(this.options.waitMillis);
						//this.remove(0);
					}
				}*/
			}, enumerable: true, configurable: true, writable: true 
		},	
		next : { value: function() {
				// edge case, shouldn't happen: both buffer and playlist is empty
				if (this.current == this.playlist.length - 1 && this.buffer.length == 0) {
					this._getMoreSongs(false, true);
					this._delay(this.options.pandora.waitMillis);
				}
				else {
					var excess = this.current - this.options.pandora.focusIndex + 1;
					while (this.playlist.length < this.options.pandora.minSongs + excess &&
					this.buffer.length > 0) {
						this.hardAdd(this.buffer.shift());
					}
					jPlayerPlaylist.prototype.next.apply(this, null);
					for (i = 0; i < excess; i++) {
						this.hardRemove(0);
					}
					if (this.buffer.length == 0) {
						var self = this;
						this._bufferSongs(function () {
							while (self.original.length < self.options.pandora.minSongs &&
							self.buffer.length) {
								self.hardAdd(self.buffer.shift());
							}
						});
					}
				}
			}, enumerable: true, configurable: true, writable: true 
		},	
		// simple remove function, none of that fancy slide up bullshit
		hardRemove : { value: function(index) {
				if (index >= 0 && index < this.original.length) {
					$(this.cssSelector.playlist + " li:nth-child(" + (index + 1) + ")").remove();
					this.original.splice(index, 1);
					this.playlist.splice(index, 1);
					if (this.original.length) {
						if (index === this.current) {
							this.current = index < this.original.length? this.current : this.original.length - 1;
							this.select(this.current);
						}
						else {
							this.current--;
						}
					}		
					else {
						$(self.cssSelector.jPlayer).jPlayer("clearMedia");
						self.current = 0;
						self._updateControls();
					}
				}
			}, enumerable: true, configurable: true, writable: true 
		},	
		hardAdd : { value: function(song, playNow) {
				$(this.cssSelector.playlist + " ul").append(this._createListItem(song)).find("li:last-child");
				this._updateControls();
				this.original.push(song);
				this.playlist.push(song);
				
				if (playNow || this.original.length === 1) {
					this.play(this.playlist.length - 1);
				}
			}, enumerable: true, configurable: true, writable: true 
		},	
		switchStation : { value: function(stationId) {
				this.remove();
				this.buffer.length = 0;
				this.currentStation = stationId;
				this._delay(this.options.pandora.delayMillis);
				this._getMoreSongs(true);
			}, enumerable: true, configurable: true, writable: true 
		},	
		currentSong : { value: function() {
				return this.playlist[this.current];
			}, enumerable: true, configurable: true, writable: true 
		},	
		//varB : { value: null, enumerable: true, configurable: true, writable: true },	
	})
})(jQuery);
