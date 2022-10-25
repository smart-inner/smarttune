package driver

import (
	"bytes"
	"database/sql"
	_ "github.com/go-sql-driver/mysql"
	tiupSpec "github.com/pingcap/tiup/pkg/cluster/spec"
	"github.com/smart-inner/smarttune/deployment"
	"gopkg.in/yaml.v2"
	"html/template"
	"strings"
)

type Driver interface {
	ChangeConf(knobs map[string]interface{}) error
}

type TiDBDriver struct {
	Tools       string
	Url         string
	ClusterName string
	Components  string
}

func (driver *TiDBDriver) ChangeConf(knobs map[string]interface{}) error {
	// modify global variables
	DB, err := sql.Open("mysql", driver.Url)
	if err != nil {
		return err
	}
	defer DB.Close()

	for key, value := range knobs {
		if strings.HasPrefix(key, "tidb.") || strings.HasPrefix(key, "tikv.") {
			continue
		}
		t, err := template.New("cmd").Parse("set @@global.{{ .Key }}={{ .Value }}")
		if err != nil {
			return err
		}
		data := struct {
			Key   string
			Value interface{}
		}{
			key,
			value,
		}
		cmd := new(bytes.Buffer)
		if err = t.Execute(cmd, data); err != nil {
			return err
		}
		if _, err = DB.Exec(cmd.String()); err != nil {
			return err
		}
	}

	// modify config knobs
	manager := &deployment.Manager{
		TiUPBinPath: driver.Tools,
	}
	topologyStr, err := manager.ShowConfig(deployment.TiUPComponentTypeCluster, driver.ClusterName, []string{}, 0)
	if err != nil {
		return err
	}
	topology := &tiupSpec.Specification{}
	if err = yaml.UnmarshalStrict([]byte(topologyStr), topology); err != nil {
		return err
	}
	for key, value := range knobs {
		if strings.HasPrefix(key, "tidb.") {
			for _, server := range topology.TiDBServers {
				if server.Config == nil {
					server.Config = make(map[string]interface{})
				}
				server.Config[key[5:]] = value
			}
		}
		if strings.HasPrefix(key, "tikv.") {
			for _, server := range topology.TiKVServers {
				if server.Config == nil {
					server.Config = make(map[string]interface{})
				}
				server.Config[key[5:]] = value
			}
		}
	}
	newTopology, err := yaml.Marshal(topology)
	if err != nil {
		return err
	}
	_, err = manager.EditConfig(deployment.TiUPComponentTypeCluster, driver.ClusterName, string(newTopology), []string{}, 0)
	if err != nil {
		return err
	}

	_, err = manager.Reload(deployment.TiUPComponentTypeCluster, driver.ClusterName, []string{"-R", driver.Components}, 0)
	if err != nil {
		return err
	}
	return nil
}
