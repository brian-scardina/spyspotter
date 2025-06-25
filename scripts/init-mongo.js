// PixelTracker MongoDB Database Initialization Script
// Creates collections, indexes, and initial data for the PixelTracker application

// Switch to pixeltracker database
db = db.getSiblingDB('pixeltracker');

print('Initializing PixelTracker MongoDB database...');

// ==========================================
// COLLECTIONS CREATION
// ==========================================

// Create scans collection
db.createCollection('scans', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["url", "scan_type", "status", "started_at"],
            properties: {
                url: {
                    bsonType: "string",
                    description: "URL being scanned"
                },
                scan_type: {
                    bsonType: "string",
                    enum: ["basic", "enhanced", "ml", "enterprise"],
                    description: "Type of scan performed"
                },
                status: {
                    bsonType: "string",
                    enum: ["pending", "running", "completed", "failed", "cancelled"],
                    description: "Current status of the scan"
                },
                started_at: {
                    bsonType: "date",
                    description: "When the scan was started"
                },
                completed_at: {
                    bsonType: ["date", "null"],
                    description: "When the scan was completed"
                },
                duration_ms: {
                    bsonType: ["int", "null"],
                    minimum: 0,
                    description: "Scan duration in milliseconds"
                },
                privacy_score: {
                    bsonType: ["int", "null"],
                    minimum: 0,
                    maximum: 100,
                    description: "Privacy score from 0-100"
                },
                risk_level: {
                    bsonType: ["string", "null"],
                    enum: ["low", "medium", "high", "critical"],
                    description: "Overall risk level"
                }
            }
        }
    }
});

// Create trackers collection
db.createCollection('trackers', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["scan_id", "tracker_type", "domain", "detected_at"],
            properties: {
                scan_id: {
                    bsonType: "objectId",
                    description: "Reference to the scan document"
                },
                tracker_type: {
                    bsonType: "string",
                    description: "Type of tracker detected"
                },
                domain: {
                    bsonType: "string",
                    description: "Domain of the tracker"
                },
                url: {
                    bsonType: ["string", "null"],
                    description: "Full URL of the tracker"
                },
                method: {
                    bsonType: ["string", "null"],
                    enum: ["pixel", "script", "iframe", "websocket", "xhr", "fetch", "beacon"],
                    description: "Method used for tracking"
                },
                risk_level: {
                    bsonType: ["string", "null"],
                    enum: ["low", "medium", "high", "critical"],
                    description: "Risk level of this tracker"
                },
                category: {
                    bsonType: ["string", "null"],
                    description: "Category of the tracker"
                },
                company: {
                    bsonType: ["string", "null"],
                    description: "Company that owns the tracker"
                },
                detected_at: {
                    bsonType: "date",
                    description: "When the tracker was detected"
                }
            }
        }
    }
});

// Create raw_data collection for storing complete scan results
db.createCollection('raw_data', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["scan_id", "data_type", "content", "created_at"],
            properties: {
                scan_id: {
                    bsonType: "objectId",
                    description: "Reference to the scan document"
                },
                data_type: {
                    bsonType: "string",
                    enum: ["html", "screenshot", "network_log", "console_log", "headers", "cookies"],
                    description: "Type of raw data stored"
                },
                content: {
                    bsonType: ["string", "object", "binData"],
                    description: "The raw content"
                },
                content_encoding: {
                    bsonType: ["string", "null"],
                    enum: ["gzip", "base64", "plain"],
                    description: "How the content is encoded"
                },
                size_bytes: {
                    bsonType: ["int", "null"],
                    minimum: 0,
                    description: "Size of the content in bytes"
                },
                created_at: {
                    bsonType: "date",
                    description: "When the data was stored"
                }
            }
        }
    }
});

// Create analytics collection for aggregated data
db.createCollection('analytics', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["date", "metric_type", "value"],
            properties: {
                date: {
                    bsonType: "date",
                    description: "Date of the metric"
                },
                metric_type: {
                    bsonType: "string",
                    description: "Type of metric"
                },
                value: {
                    bsonType: ["int", "double"],
                    description: "Metric value"
                },
                dimensions: {
                    bsonType: ["object", "null"],
                    description: "Additional dimensions for the metric"
                }
            }
        }
    }
});

// Create machine_learning collection for ML model data
db.createCollection('machine_learning', {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["model_type", "model_version", "created_at"],
            properties: {
                model_type: {
                    bsonType: "string",
                    enum: ["classifier", "clustering", "anomaly_detection", "feature_extraction"],
                    description: "Type of ML model"
                },
                model_version: {
                    bsonType: "string",
                    description: "Version of the model"
                },
                model_data: {
                    bsonType: ["object", "binData"],
                    description: "Serialized model data"
                },
                training_data_size: {
                    bsonType: ["int", "null"],
                    minimum: 0,
                    description: "Number of training samples"
                },
                accuracy_metrics: {
                    bsonType: ["object", "null"],
                    description: "Model accuracy metrics"
                },
                is_active: {
                    bsonType: "bool",
                    description: "Whether this model version is active"
                },
                created_at: {
                    bsonType: "date",
                    description: "When the model was created"
                }
            }
        }
    }
});

print('Collections created successfully');

// ==========================================
// INDEXES CREATION
// ==========================================

print('Creating indexes...');

// Scans collection indexes
db.scans.createIndex({ "url": 1 });
db.scans.createIndex({ "scan_type": 1 });
db.scans.createIndex({ "status": 1 });
db.scans.createIndex({ "started_at": -1 });
db.scans.createIndex({ "completed_at": -1 });
db.scans.createIndex({ "privacy_score": -1 });
db.scans.createIndex({ "risk_level": 1 });
db.scans.createIndex({ "url": 1, "started_at": -1 }); // Compound index

// Trackers collection indexes
db.trackers.createIndex({ "scan_id": 1 });
db.trackers.createIndex({ "domain": 1 });
db.trackers.createIndex({ "tracker_type": 1 });
db.trackers.createIndex({ "risk_level": 1 });
db.trackers.createIndex({ "category": 1 });
db.trackers.createIndex({ "company": 1 });
db.trackers.createIndex({ "detected_at": -1 });
db.trackers.createIndex({ "domain": 1, "detected_at": -1 }); // Compound index
db.trackers.createIndex({ "scan_id": 1, "tracker_type": 1 }); // Compound index

// Raw data collection indexes
db.raw_data.createIndex({ "scan_id": 1 });
db.raw_data.createIndex({ "data_type": 1 });
db.raw_data.createIndex({ "created_at": -1 });
db.raw_data.createIndex({ "scan_id": 1, "data_type": 1 }); // Compound index

// Analytics collection indexes
db.analytics.createIndex({ "date": -1 });
db.analytics.createIndex({ "metric_type": 1 });
db.analytics.createIndex({ "metric_type": 1, "date": -1 }); // Compound index

// Machine learning collection indexes
db.machine_learning.createIndex({ "model_type": 1 });
db.machine_learning.createIndex({ "model_version": 1 });
db.machine_learning.createIndex({ "is_active": 1 });
db.machine_learning.createIndex({ "created_at": -1 });
db.machine_learning.createIndex({ "model_type": 1, "is_active": 1 }); // Compound index

print('Indexes created successfully');

// ==========================================
// INITIAL DATA INSERTION
// ==========================================

print('Inserting initial data...');

// Insert sample scan data
const sampleScans = [
    {
        url: "https://example.com",
        scan_type: "basic",
        status: "completed",
        started_at: new Date(),
        completed_at: new Date(),
        duration_ms: 2500,
        privacy_score: 85,
        risk_level: "low",
        user_agent: "Mozilla/5.0 (compatible; PixelTracker/1.0)",
        metadata: {
            ip_address: "192.168.1.1",
            user_agent: "Mozilla/5.0 (compatible; PixelTracker/1.0)",
            scan_config: {
                javascript_enabled: false,
                follow_redirects: true,
                timeout: 10000
            }
        }
    }
];

db.scans.insertMany(sampleScans);

// Insert sample analytics data
const today = new Date();
const sampleAnalytics = [
    {
        date: today,
        metric_type: "scans_performed",
        value: 1,
        dimensions: {
            scan_type: "basic",
            status: "completed"
        }
    },
    {
        date: today,
        metric_type: "trackers_detected",
        value: 0,
        dimensions: {
            risk_level: "low"
        }
    }
];

db.analytics.insertMany(sampleAnalytics);

print('Initial data inserted successfully');

// ==========================================
// CREATE USERS AND PERMISSIONS
// ==========================================

print('Setting up database users and permissions...');

// Create application user with read/write permissions
db.createUser({
    user: "pixeltracker_app",
    pwd: "pixeltracker_app_password",
    roles: [
        {
            role: "readWrite",
            db: "pixeltracker"
        }
    ]
});

// Create read-only user for analytics/reporting
db.createUser({
    user: "pixeltracker_readonly",
    pwd: "pixeltracker_readonly_password",
    roles: [
        {
            role: "read",
            db: "pixeltracker"
        }
    ]
});

print('Database users created successfully');

// ==========================================
// UTILITY FUNCTIONS
// ==========================================

// Function to cleanup old data (to be called periodically)
function cleanupOldData(daysToKeep = 30) {
    const cutoffDate = new Date(Date.now() - (daysToKeep * 24 * 60 * 60 * 1000));
    
    // Remove old raw data (but keep scan records)
    const rawDataResult = db.raw_data.deleteMany({
        created_at: { $lt: cutoffDate }
    });
    
    // Remove old analytics data older than 1 year
    const yearCutoff = new Date(Date.now() - (365 * 24 * 60 * 60 * 1000));
    const analyticsResult = db.analytics.deleteMany({
        date: { $lt: yearCutoff }
    });
    
    print(`Cleanup completed:`);
    print(`- Removed ${rawDataResult.deletedCount} old raw data documents`);
    print(`- Removed ${analyticsResult.deletedCount} old analytics documents`);
    
    return {
        rawDataRemoved: rawDataResult.deletedCount,
        analyticsRemoved: analyticsResult.deletedCount
    };
}

// Function to get database statistics
function getDatabaseStats() {
    const stats = {
        scans: db.scans.countDocuments(),
        trackers: db.trackers.countDocuments(),
        rawData: db.raw_data.countDocuments(),
        analytics: db.analytics.countDocuments(),
        mlModels: db.machine_learning.countDocuments()
    };
    
    print('Database Statistics:');
    print(`- Scans: ${stats.scans}`);
    print(`- Trackers: ${stats.trackers}`);
    print(`- Raw Data: ${stats.rawData}`);
    print(`- Analytics: ${stats.analytics}`);
    print(`- ML Models: ${stats.mlModels}`);
    
    return stats;
}

// Create an admin collection to store utility functions
db.createCollection('admin_functions');
db.admin_functions.insertOne({
    _id: "utility_functions",
    cleanup_function: cleanupOldData.toString(),
    stats_function: getDatabaseStats.toString(),
    created_at: new Date(),
    description: "Utility functions for database maintenance"
});

// ==========================================
// SETUP COMPLETE
// ==========================================

print('==========================================');
print('PixelTracker MongoDB database initialization complete!');
print('');
print('Collections created:');
print('- scans (with validation schema)');
print('- trackers (with validation schema)');
print('- raw_data (with validation schema)');
print('- analytics (with validation schema)');
print('- machine_learning (with validation schema)');
print('- admin_functions');
print('');
print('Users created:');
print('- pixeltracker_app (read/write access)');
print('- pixeltracker_readonly (read-only access)');
print('');
print('Indexes created for optimal query performance');
print('Sample data inserted for testing');
print('');
print('Available utility functions:');
print('- cleanupOldData(daysToKeep): Remove old data');
print('- getDatabaseStats(): Get collection statistics');
print('==========================================');

// Display current statistics
getDatabaseStats();
