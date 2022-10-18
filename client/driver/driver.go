package driver

type Driver interface {
	ChangeConf(knobs map[string]interface{}) error
}

type TiDBDriver struct {
	Tools string
	Url   string
}

func (driver *TiDBDriver) ChangeConf(knobs map[string]interface{}) error {
	return nil
}
