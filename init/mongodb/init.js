// Create database
db = db.getSiblingDB('online_store');

// Create collections with validation
db.createCollection('events', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['event_type', 'timestamp', 'data'],
            properties: {
                event_type: {
                    bsonType: 'string',
                    enum: ['purchase', 'order_received', 'order_cancelled', 'rating_added', 'rating_updated']
                },
                timestamp: {
                    bsonType: 'date'
                },
                data: {
                    bsonType: 'object',
                    required: ['user_id', 'product_id'],
                    properties: {
                        user_id: {
                            bsonType: 'int'
                        },
                        product_id: {
                            bsonType: 'int'
                        },
                        quantity: {
                            bsonType: 'int'
                        },
                        price: {
                            bsonType: 'decimal'
                        },
                        rating: {
                            bsonType: 'decimal'
                        },
                        review: {
                            bsonType: 'string'
                        }
                    }
                }
            }
        }
    }
});

// Create indexes
db.events.createIndex({ 'timestamp': 1 });
db.events.createIndex({ 'event_type': 1 });
db.events.createIndex({ 'data.user_id': 1 });
db.events.createIndex({ 'data.product_id': 1 });

// Create TTL index to automatically delete events older than 1 year
db.events.createIndex(
    { 'timestamp': 1 },
    { expireAfterSeconds: 31536000 } // 1 year in seconds
); 