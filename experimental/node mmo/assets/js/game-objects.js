class Entity{
	constructor(sprite) {
		this.sprite = sprite;
		this.x = 0; //Relative to the world
		this.y = 0; //Relative to the world
		this.v_angle = 0;
		this.angle = 0;
		this.width = sprite.width;
		this.height = sprite.height;
	}

	get_position() {
		return [this.x, this.y];
	}

	set_position(position) {
		[this.x, this.y] = position;
	}
}

export class Tile extends Entity {
	constructor(sprite) {
		super(sprite);
	}
}

export class Player extends Entity {
	constructor(sprite) {
		super(sprite);
		this.player_id = null;
		this.tween_time = -1;
		this.tween_x = 0;
		this.tween_y = 0;
		this.tween_angle = 0;

		// Client Prediction
		this.pressingRight = false;
		this.pressingLeft = false;
		this.pressingUp =false;
		this.pressingDown = false;
		this.maxSpeed = 10;
	}

	getInputs(){
		var inputs = [];
		if (this.pressingUp) {
			inputs.push(0);
		}
		if (this.pressingDown) {
			inputs.push(1);
		}
		if (this.pressingLeft) {
			inputs.push(2);
		}
		if (this.pressingRight) {
			inputs.push(3);
		}
		return inputs;
	}

	tween_to(x, y, angle) {
		this.tween_time = 0;
		this.tween_x = x;
		this.tween_y = y;
		this.tween_angle = angle;
	}

	lerp(v0, v1, t){
		return (1-t)*v0 + v1*t
	}

	lerp_angle(v0, v1, t){
		var dif = (v1-v0)%(2*Math.PI)
		return (dif*t + v0)%(2*Math.PI);
	}

	// Client Prediction
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
		this.tween_to(this.x+move_vector[0], this.y+move_vector[1], this.angle);
	}

	update(delta) {
		if (this.tween_time > -1) {
			this.tween_time += 0.5*delta;
			if (this.tween_time > 1) {
				this.tween_time = 1;
			}
			this.x = this.lerp(this.x, this.tween_x, this.tween_time);
			this.y = this.lerp(this.y, this.tween_y, this.tween_time);
			this.angle = this.lerp_angle(this.angle, this.tween_angle, this.tween_time);
			if (this.tween_time == 1) {
				this.tween_time = -1;
				this.tween_x = this.x;
				this.tween_y = this.y;
				this.tween_angle = this.angle;
			}
		}
	}
}

export class Camera{
	constructor(width, height) {
		this.x = 0;
		this.y = 0;
		this.width = width;
		this.height = height;
	}

	translate_position(position) {
		position[0] -= this.x - this.width/2;
		position[1] = - position[1] + this.height/2  + this.y; //Flip the y-axis because pixi is inverted in the y-axis
		return position;
	}
}