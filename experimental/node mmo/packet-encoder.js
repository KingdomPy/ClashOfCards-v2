op_codes = {
	"join": 0, // Selected character
	"input": 1, // Input type
	"sendMessage": 2, // Message
	"logMessage": 3, // Message
	"addEntity": 4, // Id and position + character
	"updateEntity": 5, // Id and position + animation
	"removeEntity": 6, // Id
	"setid": 7, // Id
	"getEntity": 8, // Id
};

key_codes = {
	"keyboard": 0,
	"mouse": 1,
};

entity_codes = {
	"player": 0,
	"beast": 1,
	"knight": 2,
	"knuckles": 3,
	"portal": 4,
	"unknown": 5,
};

module.exports.op_codes = op_codes;
module.exports.key_codes = key_codes;
module.exports.entity_codes = entity_codes;

