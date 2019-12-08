import { Camera, Tile, Player } from '/assets/js/game-objects.js'
import { op_codes, key_codes, entity_codes } from '/assets/js/packet-encoder.js'

//Aliases
let Application = PIXI.Application,
	loader = PIXI.Loader.shared,
	resources = PIXI.Loader.shared.resources,
	Sprite = PIXI.Sprite;
// The application will create a renderer using WebGL, if possible,
// with a fallback to a canvas render. It will also setup the ticker
// and the root stage PIXI.Container

var resolution = window.innerHeight/900;

const app = new Application({
	width: 1600,
	height: 900,
	antialias: true,
	transparent: false,
	resolution: resolution,
});
app.stage.interactive = true;

const width = 1600;
const height = 900;

let camera = new Camera(width, height);

let game_state;

let timeStart;
let elapsedTime;

let tiles = [];
let entities = [];
let player;
let input_log =[];
let input_sequence = 0;
let character;
let my_id;
var socket = io();;

// DOM attatchers
var chat_messages = document.getElementById("chat-messages");
var message_entry = document.getElementById("message-entry");
var send_button = document.getElementById("message-submit");

// The application will create a canvas element for you that you
// can then insert into the DOM
document.getElementById("app").appendChild(app.view);
// Center the canvas
var margin = "0px "+ (window.innerWidth-width*resolution)/2 + "px";
app.view.style.margin = margin;
document.getElementById("chat-box").style.margin = margin;
document.getElementById("message-box").style.margin = margin;


loader
	.add("/assets/img/tiles/stone.png")
	.add("/assets/img/tiles/white.png")
	.add("/assets/img/tiles/green.png")
	.add("/assets/img/tiles/red.png")
	.add("/assets/img/player.png")
	.add("/assets/img/knight.png")
	.add("/assets/img/beast.png")
	.add("/assets/img/knuckles.png")
	.add("/assets/img/portal.png")
	.add("/assets/img/unknown.png")
	.on("progress", loadProgressHandler)
	.load(setup);

function loadProgressHandler(loader, resource) {
  console.log("loading: " + resource.url); 
  console.log("progress: " + loader.progress + "%"); 
}

function setup() {
	for (var i = 0; i < 11; i++) {
		for (var j = 0; j < 40; j++) {
			if (j < 2) {
				var tile = new Sprite(resources["/assets/img/tiles/green.png"].texture);
			} else if (j > 37){
				var tile = new Sprite(resources["/assets/img/tiles/red.png"].texture);
			} else{
				var tile = new Sprite(resources["/assets/img/tiles/white.png"].texture);
			}
			tile = new Tile(tile);
			tiles.push(tile);
			tile.set_position([tile.width*j, tile.height*i]);
			tile.sprite.position.set(tile.width*j, tile.height*i);
			app.stage.addChild(tile.sprite);
		}}

	setupSocket(); //Set up the Websocket functions

	// Set the game state
	game_state = selectCharacter;

	app.ticker.add(function(delta){
		update(delta);
	});
}

function update(delta) {
	game_state(delta);
}

function sendMessage(){
	let message = message_entry.value;
	if (message != "") {
		socket.emit(op_codes['sendMessage'], message);
	}
	message_entry.value = "";
}

function setupSocket(){
	send_button.onclick = sendMessage;
	
	socket.on(op_codes['setid'], function(data){
		my_id = data;
		player.player_id = my_id;
	});

	socket.on(op_codes['addEntity'], function(packet){
		let data;
		let entity;
		let circle;
		for (var i = 0; i < packet.length; i++) {
			data = packet[i];
			if(data.type == "player"){
				let sprite = data.character;
				for(let key in entity_codes){
					if (entity_codes[key] == sprite) {
						sprite = key;
						break;
					}
				}
				entity = new Sprite(resources["/assets/img/"+sprite+".png"].texture);
				entity = new Player(entity);
				entity.player_id = data.id;
				entity.set_position([data.x, data.y]);
				entities.push(entity);
				app.stage.addChild(entity.sprite);
				app.stage.sortChildren();
			} else{
				circle = new PIXI.Graphics();
				circle.beginFill(0x66CCFF);
				circle.lineStyle(4, 0xFF3300, 1);
				circle.drawCircle(0, 0, data.radius);
				circle.endFill();
				circle = new Player(circle);
				circle.player_id = data.id;
				entities.push(circle);
				app.stage.addChild(circle.sprite);
				app.stage.sortChildren();
			}
		}
	});

	socket.on(op_codes['updateEntity'], function(data){
		for (var i=0; i < data.length; i++) {
			let entity_id = data[i].id;
			let exists = false;
			for (var j=0; j < entities.length; j++) {
				if (entity_id == entities[j].player_id) {
					if (my_id == entity_id) {
						var sequence = data[i].sq;
						for (var k=0; k < input_log.length; k++) {
							if (sequence == input_log[k]) {
								input_log.splice(0, k+1); // Remove previous inputs
								if (input_log.length == 0) { // Up to date
									entities[j].tween_to(data[i].x, data[i].y, 0); 
									exists = true;
									break;
								}
							}
						}
					}
					entities[j].tween_to(data[i].x, data[i].y, 0);
					exists = true;
					break;
				} 
			}
			if (!exists) {
				// socket.emit(op_codes['getEntity'], entity_id);
			}
		}	
	});

	socket.on(op_codes['logMessage'], function(message) {
		chat_messages.innerHTML += '<li>'+message+'</li>';
	});

	socket.on(op_codes['removeEntity'], function(id) {
		for (var i = 0; i < entities.length; i++) {
			if (id == entities[i].player_id) {
				app.stage.removeChild(entities[i].sprite);
				entities.splice(i, 1);
				break;
			}
		}
	});

	message_entry.addEventListener("keyup", function(event) {
		if(event.keyCode === 13) {
			event.preventDefault();
			sendMessage();
		}
	});

	document.onkeydown = function(event){
		if (event.keyCode === 68) {
			player.pressingRight = true;			
		}
		else if (event.keyCode === 83) {
			player.pressingDown = true;			
		}
		else if (event.keyCode === 65) {
			player.pressingLeft = true;			
		}
		else if (event.keyCode === 87) {
			player.pressingUp = true;		
		}
	};

	document.onkeyup = function(event){
		if (event.keyCode === 68) {
			player.pressingRight = false;
		}
		else if (event.keyCode === 83) {
			player.pressingDown = false;			
		}
		else if (event.keyCode === 65) {
			player.pressingLeft = false;
		}
		else if (event.keyCode === 87) {
			player.pressingUp = false;
		}
	};

	// Client prediction
	setInterval(function(){
		if (typeof player != "undefined") {
			var keys = player.getInputs();
			if (keys.length > 0) {
				socket.emit(op_codes["input"], {sq:input_sequence, keys:keys});
				input_log.push(input_sequence);
				input_sequence += 1;
				player.updatePosition();

			} else{
				input_sequence = 0;
			}
		}
	}, 16);
}

function selectCharacter(delta){
	character = document.getElementById("selected-character").innerHTML;
	if (character != "") {
		socket.emit(op_codes['join'], entity_codes[character]);
		document.getElementById("home").style.display = "none";
		document.getElementById("app").style.display = "block";

		player = new Sprite(resources["/assets/img/"+character+".png"].texture);
		player.zIndex = 1;
		player = new Player(player);
		player.set_position([0, 0]);
		player.sprite.position.set((width - player.width)/2, (height - player.height)/2);
		entities.push(player);
		app.stage.addChild(player.sprite);

		timeStart= Date.now();
		game_state = play;
	}
}

function play(delta){
	elapsedTime = Date.now()-timeStart;
	player.update(delta);
	camera.x = player.x;
	camera.y = player.y;
	for(var i=0; i < tiles.length; i++){
		var position = tiles[i].get_position();
		var [sprite_x, sprite_y] = camera.translate_position(tiles[i].get_position());
		tiles[i].sprite.position.set(sprite_x, sprite_y);
	}
	for(var i=0; i < entities.length; i++){
		if (my_id != entities[i].player_id) {
			entities[i].update(delta);
		}
		var [sprite_x, sprite_y] = camera.translate_position(entities[i].get_position());
		entities[i].sprite.position.set(sprite_x, sprite_y);
	}
}



