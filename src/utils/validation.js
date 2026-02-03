const passwordValidator = require("password-validator");

const schema = new passwordValidator();
schema.is().min(8)
    .is().max(20)
    .has().uppercase()
    .has().lowercase()
    .has().digits(1)
    .has().not().spaces();

module.exports = schema;
