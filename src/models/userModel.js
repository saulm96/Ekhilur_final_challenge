import { DataTypes} from "sequelize";
import sequelize from "../config/sequelize.js";

const User = sequelize.define("users", {
    user_id: {
        type: DataTypes.INTEGER.UNSIGNED,
        primaryKey: true,
        autoIncrement: true,
        allowNull: false,
    },
    name: {
        type: DataTypes.STRING(100),
        allowNull: false,
    },
    email: {
        type: DataTypes.STRING(100),
        allowNull: false,
        unique: true,
    },
    password: {
        type: DataTypes.STRING(150),
        allowNull: false,
    },
    two_factor_secret: {
        type: DataTypes.STRING(255),
        allowNull: true,
    },
    two_factor_enabled: {
        type: DataTypes.BOOLEAN,
        allowNull: false,
        defaultValue: false,
    },
    role: {
        type: DataTypes.ENUM('admin', 'user', 'council'),
        allowNull: false,
        defaultValue: 'user',
    }
});

export default User;