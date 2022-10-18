package deployment

// TiUPComponentType Type of TiUP component, e.g. cluster/dm/tiem
type TiUPComponentType string

const (
	TiUPComponentTypeCluster TiUPComponentType = "cluster"
)

type TiUPMeta struct {
	Component string
	Servers   []*interface{}
}

const (
	CMDShowConfig   = "show-config"
	CMDEditConfig   = "edit-config"
	CMDReload       = "reload"
	FlagWaitTimeout = "--wait-timeout"
	CMDYes          = "--yes"
	CMDTopologyFile = "--topology-file"
)

type Deployment interface {
	Reload(componentType TiUPComponentType, clusterName string, args []string, timeout int) (result string, err error)
	EditConfig(componentType TiUPComponentType, clusterName, configYaml string, args []string, timeout int) (result string, err error)
	ShowConfig(componentType TiUPComponentType, clusterName string, args []string, timeout int) (result string, err error)
}
