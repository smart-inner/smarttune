package collector

import (
	"database/sql"
	"encoding/json"
	_ "github.com/go-sql-driver/mysql"
	"strings"
)

type Collector interface {
	CollectKnobs() (string, error)
	CollectMetrics() (string, error)
}

type TiDBCollector struct {
	Url string
}

func (collector *TiDBCollector) CollectKnobs() (string, error) {
	DB, err := sql.Open("mysql", collector.Url)
	if err != nil {
		return "", err
	}
	defer DB.Close()
	globalKnobs := make(map[string]string)

	// collect tidb configuration
	rows, err := DB.Query("SHOW CONFIG;")
	if err != nil {
		return "", nil
	}
	for rows.Next() {
		var Type string
		var Instance string
		var Name string
		var Value string
		if err = rows.Scan(&Type, &Instance, &Name, &Value); err != nil {
			return "", err
		}
		key := strings.Join([]string{Type, Name}, ".")
		if _, ok := globalKnobs[key]; !ok {
			globalKnobs[key] = Value
		}
	}

	// collect tidb global variables
	rows, err = DB.Query("SHOW GLOBAL VARIABLES;")
	if err != nil {
		return "", err
	}
	for rows.Next() {
		var VariableName string
		var Value string
		if err = rows.Scan(&VariableName, &Value); err != nil {
			return "", err
		}
		if _, ok := globalKnobs[VariableName]; !ok {
			globalKnobs[VariableName] = Value
		}
	}
	knobs := make(map[string]interface{})
	knobs["global"] = globalKnobs
	knobs["local"] = nil
	result, err := json.Marshal(knobs)
	if err != nil {
		return "", err
	}
	return string(result), nil
}

func (collector *TiDBCollector) CollectMetrics() (string, error) {
	DB, err := sql.Open("mysql", collector.Url)
	if err != nil {
		return "", err
	}
	defer DB.Close()
	globalMetrics := make(map[string]string)
	MetricsSQL := map[string]string{
		"tidb.tidb_qps": "SELECT sum(value)/7 'value' from METRICS_SCHEMA.tidb_qps where " +
			"result='OK' and time between now()-interval 4 minute and now()-interval 1 minute;",
		"tidb.tidb_query_duration": "SELECT avg(value) 'value' from METRICS_SCHEMA.tidb_query_duration " +
			"where quantile=0.99 and time between now()-interval 4 minute and now()-interval 1 minute;",
	}
	// set tidb_metric_query_duration and tidb_metric_query_step to 30 sec
	if _, err = DB.Exec("set@@tidb_metric_query_range_duration=30;"); err != nil {
		return "", err
	}
	if _, err = DB.Exec("set@@tidb_metric_query_step=30;"); err != nil {
		return "", err
	}
	for key, value := range MetricsSQL {
		rows, err := DB.Query(value)
		if err != nil {
			return "", err
		}
		for rows.Next() {
			var Value string
			if err = rows.Scan(&Value); err != nil {
				return "", err
			}
			if _, ok := globalMetrics[key]; !ok {
				globalMetrics[key] = Value
			}
		}
	}
	metrics := make(map[string]interface{})
	metrics["global"] = globalMetrics
	metrics["local"] = nil
	result, err := json.Marshal(metrics)
	if err != nil {
		return "", err
	}
	return string(result), nil
}
