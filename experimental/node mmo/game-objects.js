class entity{
	constructor(entity_id) {
		this.x = 0;
		this.y = 0;
		this.angle = 0.5;
		this.id = entity_id;
		this.inputSequence = 0;
	}

	update(){
		var [x, y, angle] = [this.x, this.y, this.angle];
		this.updatePosition();
		if (x == this.x && y == this.y && angle == this.angle) {
			return 0;
		}
		return {sq:this.inputSequence, id:this.id, x:this.x, y:this.y};
	}
}

class player extends entity{
	constructor(entity_id) {
		super(entity_id);
		this.character = "player";
		this.resetInputs();
		this.maxSpeed = 10;
	}

	getData(){
		return {id:this.id, type:"player", character:this.character, x:this.x, y:this.y};
	}

	resetInputs(){
		this.canInput = true;
		this.pressingRight = false;
		this.pressingLeft = false;
		this.pressingUp =false;
		this.pressingDown = false;
	}

	setCharacter(character) {
		this.character = character;
	}

	updatePosition() {
		let move_vector = [0 ,0];
		if (this.pressingUp) {
			move_vector[1] += this.maxSpeed
		}
		if (this.pressingDown) {
			move_vector[1] -= this.maxSpeed
		}
		if (this.pressingRight) {
			if(move_vector[1] != 0) {
				move_vector[1] *= 0.70711;
				move_vector[0] += this.maxSpeed*0.70711;
			}else{
				move_vector[0] += this.maxSpeed
			}
		}
		if (this.pressingLeft) {
			if(move_vector[1] != 0) {
				if (this.pressingRight) {
					move_vector[1] *= (1/0.70711);
					move_vector[0] -= this.maxSpeed*0.70711;
				}else{
					move_vector[1] *= 0.70711;
					move_vector[0] -= this.maxSpeed*0.70711;
				}
			}else{
				move_vector[0] -= this.maxSpeed
			}
		}
		this.x += move_vector[0];
		this.y += move_vector[1];
		this.resetInputs();
	}
}

class enemy extends entity{
	constructor(entity_id) {
		super(entity_id);
		this.maxSpeed = 8;
		this.radius = 64;
	}

	getData() {
		return {id:this.id, type:"enemy", radius:this.radius, x:this.x, y:this.y};
	}

	updatePosition() {
		this.x += Math.cos(this.angle) * this.maxSpeed;
		this.y += Math.sin(this.angle) * this.maxSpeed;	
	}

	update() {
		return {id:this.id, x:this.x, y:this.y};
	}
}

module.exports.Player = player;
module.exports.Enemy = enemy;